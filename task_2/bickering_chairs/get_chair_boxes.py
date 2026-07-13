import cv2
import os

WINDOW_NAME = "Chair-Setup"

class ChairZoneSelector:
    def __init__(self, cap, expectedChars):
        self.cap = cap
        self.chair_boxes = []
        self.expected = expectedChars
        
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.current_box = None

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
            self.current_box = [x, y, x, y]

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                x1, y1 = min(self.ix, x), min(self.iy, y)
                x2, y2 = max(self.ix, x), max(self.iy, y)
                self.current_box = [x1, y1, x2, y2]

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False


    def run(self):
        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self.mouse_callback)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1) 
            
            for i, box in enumerate(self.chair_boxes):
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
                cv2.putText(frame, f"Chair {i}", (box[0], box[1] - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            if self.current_box:
                cv2.rectangle(frame, (self.current_box[0], self.current_box[1]), 
                              (self.current_box[2], self.current_box[3]), (255, 0, 0), 2)
                
            text = f"Selected {len(self.chair_boxes)}"
            if self.expected > 1:
                text += f"from {self.expected}"
            text += " Boxes | Press 'ESC' to clear them | Press 'Space' to select the next box | Press 'Enter' Once done |'Q' to exit"
            cv2.putText(frame, text, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('d'):
                self.chair_boxes.clear()
            elif key == 32:  #Space    
                #COULD TODO: if one adds 2 speakers to laptop one could get the id of them here and safe them according to the selected chair
                if self.current_box is not None:
                    self.chair_boxes.append(tuple(self.current_box))
                    print(f"-> Box {len(self.chair_boxes)-1} added: {tuple(self.current_box)}")
                    self.current_box = None 
            elif key == 13:  #Enter
                if len(self.chair_boxes) >= self.expected and len(self.chair_boxes) > 0 and len(self.chair_boxes) < 3:
                        break
                else:
                    print("You need atleast one and max 2 Rectangles")

            elif key == ord("q"):
                os._exit(0)

        cv2.destroyAllWindows()
        return self.chair_boxes