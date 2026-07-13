import os
import cv2
import numpy as np
import xml.etree.ElementTree as ET
import pyglet
import math
import argparse
from PIL import Image
from tqdm import tqdm
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from collections import deque
from recognizer import DollarRecognizer, Point


MEDIAPIPE_HAND_LANDMARK_MODEL_PATH = "hand_landmarker.task"
XML_LOGS = 'task_2/air_writing/datasets'
NUMBER_OF_POINTS = 64
LETTERS_TO_TRAIN = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def train_recognizer(recognizer):
    for root, subdirs, files in os.walk(XML_LOGS):
        for f in tqdm(files):
            if '.xml' in f:
                fname = f.split('.')[0]
                label = fname.rsplit("_", 1)[0]
                if label not in LETTERS_TO_TRAIN:
                    continue

                xml_root = ET.parse(f'{root}/{f}').getroot()

                points = []
                for element in xml_root.findall('Point'):
                    x = element.get('X')
                    y = element.get('Y')
                    points.append(Point(float(x), float(y)))

                recognizer.addGesture(label, points)


class HandDetector:
    """This class uses the MediaPipe Hand Landmark model to detect hands in the video feed and return bounding boxes around them.
    Made with tutorial https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker
    """

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, MEDIAPIPE_HAND_LANDMARK_MODEL_PATH)
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options, num_hands=2)
        self.detector = vision.HandLandmarker.create_from_options(options)

    def detect_box(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )
        results = self.detector.detect(mp_image)

        # Getting the bounding box was assisted by ChatGPT
        if results.hand_landmarks:
            hand_landmarks = results.hand_landmarks[0]

            h, w, _ = frame.shape

            xs = [lm.x for lm in hand_landmarks]
            ys = [lm.y for lm in hand_landmarks]

            x1 = int(min(xs) * w)
            y1 = int(min(ys) * h)
            x2 = int(max(xs) * w)
            y2 = int(max(ys) * h)

            padding = 30
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)

            box = (x1, y1, x2, y2)

            return box, hand_landmarks

        return None, None


class WritingApp:

    def __init__(self, video_id=0, mac_os=True):
        self.video_id = video_id
        self.detector = HandDetector()
        self.recognizer = DollarRecognizer()
        train_recognizer(self.recognizer)
        self.cap = cv2.VideoCapture(self.video_id)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.is_writing = False
        self.points = deque(maxlen=512)
        self.ar_threshold = 1.2
        self.reference_point = None
        self.current_frame = None
        self.region_factor = 0.2
        self.selected_color = (0, 255, 255)
        self.is_erasing = False
        self.pen_size = 12
        self.fps = None
        self.current_stroke = []
        self.detected_letter = None
        self.pen_down_frame = 0
        self.pen_down_frames_threshold = 5
        if mac_os:
            self.window = pyglet.window.Window(
                (self.width / 2), (self.height / 2))
        else:
            self.window = pyglet.window.Window(self.width, self.height)
        self.setup_tools()

    def setup_tools(self):
        # Setup tools for writing
        tool_box_w = self.width // 8
        tool_box_h = int((self.height * self.region_factor) * 0.8)

        padding_horizontal = tool_box_w // 8
        padding_vertical = int(
            ((self.height * self.region_factor) - tool_box_h) // 2)

        self.tools = {}
        tool_data = [("Eraser", (255, 255, 255)), ("Blue", (255, 0, 0)), ("Green", (0, 255, 0)),
                     ("Red", (0, 0, 255)), ("Yellow", (0, 255, 255)), ("Clear", (0, 0, 0))]

        for i, (name, color) in enumerate(tool_data):
            x1 = i * tool_box_w + padding_horizontal * (i + 1)
            y1 = 0 + padding_vertical
            x2 = x1 + tool_box_w
            y2 = y1 + tool_box_h
            self.tools[name] = {
                "box": (x1, y1, x2, y2),
                "color": color
            }

        self.utils = {}
        x = len(self.tools) * tool_box_w + \
            padding_horizontal * (len(self.tools) + 1)
        self.utils["+"] = {
            "box": (x, padding_vertical, x + int(tool_box_w // 2), padding_vertical + tool_box_h),
            "color": (255, 255, 255)
        }
        self.utils["-"] = {
            "box": (x + int(tool_box_w // 2), padding_vertical, x + tool_box_w, padding_vertical + tool_box_h),
            "color": (255, 255, 255)
        }

    def draw_tools(self, frame):
        for name, tool in self.tools.items():
            overlay = frame.copy()
            x1, y1, x2, y2 = tool["box"]
            color = tool["color"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            cv2.putText(frame, name, (x1 + 10, y1 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color,  2)
            alpha = 0.4
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        for name, util in self.utils.items():
            overlay = frame.copy()
            x1, y1, x2, y2 = util["box"]
            color = util["color"]
            (text_width, text_height), baseline = cv2.getTextSize(
                name, cv2.FONT_HERSHEY_SIMPLEX, 3, 2)
            offset = int(text_height * 0.2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            cv2.putText(frame, name, (x1 + (x2 - x1) // 2 - text_width // 2, y1 + (y2 - y1) // 2 + text_height // 2 - offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 3, color, 2)
            alpha = 0.4
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def on_draw(self):
        self.window.clear()
        if self.current_frame is not None:
            frame = self.current_frame.copy()
            self.draw_tools(frame)
            if self.reference_point is not None:
                cv2.circle(frame, self.reference_point,
                           self.pen_size, self.selected_color, -1)
            cv2.putText(frame, f"FPS: {self.fps:.2f}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            self.draw_points(frame)
            if self.detected_letter is not None:
                cv2.putText(frame, f"Detected: {self.detected_letter}", (10, 400),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2, cv2.LINE_AA)
            img = cv2glet(frame, 'BGR')
            img.blit(0, 0, 0)

    def draw_points(self, frame):
        points_to_draw = list(self.points)

        for i in range(1, len(points_to_draw)):
            point = points_to_draw[i]
            prev_point = points_to_draw[i - 1]

            if prev_point is None or point is None:
                continue

            cv2.line(frame, prev_point["point"],
                     point["point"], point["color"], point["size"])

    def update(self, dt):
        self.fps = 1.0 / dt
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return
        frame = cv2.flip(frame, 1)
        box, hand_landmarks = self.detector.detect_box(frame)
        self.current_frame = frame

        if box is not None:
            # Hand is dtetected, get the reference point and check if it's in the writing region
            self.reference_point = self.get_reference_point(box)

            if self.reference_point[1] >= self.height * self.region_factor:
                # Hand is in the writing region, check if it's writing or erasing
                self.is_writing = self.aspect_ratio_greater_than_threshold(box)

                if self.is_erasing:
                    self.is_writing = False
                    self.pen_down_frame = 0
                    self.erase_points()

                elif self.is_writing:
                    # Hand is writing, add the reference point to the points list and current stroke
                    self.pen_down_frame = 0
                    self.points.append({
                        "point": self.reference_point,
                        "color": self.selected_color,
                        "size": self.pen_size
                    })
                    self.current_stroke.append(self.reference_point)

                elif self.current_stroke:
                    # Hand is not writing, but there is a current stroke, check if pen is down for enough frames
                    self.pen_down_frame += 1
                    if self.pen_down_frame >= self.pen_down_frames_threshold:
                        self.add_breakpoint()
                        self.finish_stroke()
                        self.pen_down_frame = 0
                else:
                    # Hand is not writing and there is no current stroke
                    self.add_breakpoint()
            else:
                # Hand is not in the writing region
                self.is_writing = False
                self.add_breakpoint()
                if self.current_stroke:
                    self.pen_down_frame += 1
                    if self.pen_down_frame >= self.pen_down_frames_threshold:
                        self.finish_stroke()
                        self.pen_down_frame = 0

                tool_name = self.check_tool_selection()
                if tool_name:
                    self.handle_tool_selection(tool_name)
        else:
            # Hand is not detected
            self.reference_point = None
            self.is_writing = False
            self.add_breakpoint()
            if not self.current_stroke:
                self.pen_down_frame = 0
                return

            self.pen_down_frame += 1
            if self.pen_down_frame >= self.pen_down_frames_threshold:
                self.finish_stroke()
                self.pen_down_frame = 0

    def handle_tool_selection(self, tool_name):
        if tool_name == "Clear":
            self.current_stroke.clear()
            self.pen_down_frame = 0
            self.points.clear()
        elif tool_name == "Eraser":
            self.is_erasing = True
            self.selected_color = self.tools[tool_name]["color"]
        elif tool_name == "-":
            self.pen_size = max(1, self.pen_size - 2)
        elif tool_name == "+":
            self.pen_size = min(50, self.pen_size + 2)
        else:
            self.selected_color = self.tools[tool_name]["color"]
            self.is_erasing = False

    def finish_stroke(self):
        if len(self.current_stroke) < 10:
            self.current_stroke.clear()
            return

        points_copy = self.convert_stroke_to_points()
        result = self.recognizer.recognize(points_copy, useProtractor=True)
        self.detected_letter = result.name
        print(f"Detected letter: {result.name} with score: {result.score:.2f}")
        self.current_stroke.clear()

    def convert_stroke_to_points(self):
        points = []
        for p in self.current_stroke:
            points.append(Point(p[0], (self.height - p[1])))
        return points

    def add_breakpoint(self):
        if self.points and self.points[-1] is not None:
            self.points.append(None)

    def get_aspect_ratio(self, box):
        x1, y1, x2, y2 = box
        width = x2 - x1
        height = y2 - y1

        if width <= 0:
            return

        return height / width

    def aspect_ratio_greater_than_threshold(self, box):
        aspect_ratio = self.get_aspect_ratio(box)
        return aspect_ratio > self.ar_threshold

    def get_reference_point(self, box):
        x1, y1, x2, y2 = box
        x = (x1 + x2) // 2
        y = y1
        return (x, y)

    def check_tool_selection(self):
        x, y = self.reference_point
        for name, tool in self.tools.items():
            x1, y1, x2, y2 = tool["box"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        for name, util in self.utils.items():
            x1, y1, x2, y2 = util["box"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return None

    def erase_points(self):

        if self.reference_point is None:
            return

        points = list(self.points)

        for i, p in enumerate(points):
            if p is not None:
                point = p["point"]
                distance = math.dist(point, self.reference_point)
                if distance <= self.pen_size:
                    points[i] = None

        self.points = deque(points, maxlen=self.points.maxlen)


def cv2glet(img, fmt):
    '''Assumes image is in BGR color space. Returns a pyimg object'''
    if fmt == 'GRAY':
        rows, cols = img.shape
        channels = 1
    else:
        rows, cols, channels = img.shape

    raw_img = Image.fromarray(img).tobytes()

    top_to_bottom_flag = -1
    bytes_per_row = channels*cols
    pyimg = pyglet.image.ImageData(width=cols,
                                   height=rows,
                                   fmt=fmt,
                                   data=raw_img,
                                   pitch=top_to_bottom_flag*bytes_per_row)
    return pyimg


def main():
    app = WritingApp()

    @app.window.event
    def on_draw():
        app.on_draw()

    @app.window.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            app.cap.release()
            app.detector.detector.close()
            pyglet.app.exit()
    pyglet.clock.schedule_interval(app.update, 1/30)
    pyglet.app.run()


if __name__ == "__main__":
    main()
