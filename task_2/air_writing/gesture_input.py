# gesture input program for first task
import os
from recognizer import Point
import xml.etree.ElementTree as ET
import pyglet
import time as time

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
XML_LOGS_OWN = 'task_2/air_writing/datasets'


def get_next_file_name(name):
    os.makedirs(XML_LOGS_OWN, exist_ok=True)
    # Made With ChatGPT
    existing_files = [f for f in os.listdir(
        XML_LOGS_OWN) if f.startswith(name) and f.endswith('.xml')]
    if not existing_files:
        return f"{name}_01.xml"

    max_index = 0
    for f in existing_files:
        try:
            index = int(f.split('_')[-1].split('.')[0])
            max_index = max(max_index, index)
        except ValueError:
            continue

    return f"{name}_{max_index + 1:02d}.xml"


class GestureInputApp:
    def __init__(self):
        self.width = 800
        self.height = 800
        self.points = []
        self.draw_points = []
        self.timestamps = []
        self.alphabet_index = 0
        self.current_letter = ALPHABET[self.alphabet_index]
        self.gesture_label = pyglet.text.Label(
            f"Draw {self.current_letter} — press S to save",
            font_size=24,
            x=40,
            y=self.height - 60
        )

        self.window = pyglet.window.Window(self.width, self.height)
    
    def on_draw(self):
        self.window.clear()
        self.gesture_label.draw()
        if len(self.points) < 2:
            return
        coords = []
        for p in self.draw_points:
            coords.append((p.x, p.y))
        line = pyglet.shapes.MultiLine(*coords, thickness=2, color=(255, 0, 0))
        line.draw()

    def append_points(self, x, y):
        t = int(time.time() * 1000)

        point_to_add = Point(x, self.height - y)

        if len(self.points) > 0:
            last_point = self.points[-1]

            if point_to_add.x == last_point.x and point_to_add.y == last_point.y:
                return

        self.points.append(point_to_add)
        self.draw_points.append(Point(x, y))
        self.timestamps.append(t)

    def on_mouse_press(self, x, y, button, modifiers):
        self.points = []
        self.draw_points = []
        self.timestamps = []
        self.append_points(x, y)
        
    def reset_current_gesture(self):

        self.points.clear()
        self.draw_points.clear()
        self.timestamps.clear()

    def save_gesture(self):
        os.makedirs(XML_LOGS_OWN, exist_ok=True)

        root = ET.Element("Gesture", {
            "Name": self.current_letter,
            "NumPts": str(len(self.points))
        })
        for i, p in enumerate(self.points):
            point_element = ET.SubElement(root, "Point")
            point_element.set("X", str(p.x))
            point_element.set("Y", str(p.y))
            point_element.set("T", str(self.timestamps[i]))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(f"{XML_LOGS_OWN}/{get_next_file_name(self.current_letter)}",
                   encoding='utf-8', xml_declaration=True)

        self.reset_current_gesture()
        
    def next_letter(self):
        self.alphabet_index = (self.alphabet_index + 1) % len(ALPHABET)
        self.current_letter = ALPHABET[self.alphabet_index]
        self.reset_current_gesture()
        self.gesture_label.text = f"Draw {self.current_letter} — press S to save"

def main():
    app = GestureInputApp()

    @app.window.event
    def on_draw():
        app.on_draw()

    @app.window.event
    def on_mouse_press(x, y, button, modifiers):
        app.on_mouse_press(x, y, button, modifiers)
        pass

    @app.window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        app.append_points(x, y)
        pass

    @app.window.event
    def on_mouse_release(x, y, buttons, modifiers):
        app.append_points(x, y)
        pass

    @app.window.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()
        if symbol == pyglet.window.key.S:
            app.save_gesture()
        if symbol == pyglet.window.key.R:
            app.reset_current_gesture()
        if symbol == pyglet.window.key.N:
            app.next_letter()

    pyglet.app.run()


if __name__ == '__main__':
    main()
