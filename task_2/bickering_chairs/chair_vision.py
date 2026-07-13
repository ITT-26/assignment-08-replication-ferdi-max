import cv2
from get_chair_boxes import ChairZoneSelector
import mediapipe as mp
from mediapipe.tasks import python
import os
from mediapipe.tasks.python import vision
import time
import numpy as np
import threading
import face_recognition
from dataclasses import dataclass, field
import math

#Note:
# - This class is an abomination
# - My brain still hurts a little

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FACE_MODEL_PATH = os.path.join(SCRIPT_DIR, "models/face_landmarker.task") #Don't know why it wouldn't work with realative path
FACE_OPTIONS = vision.FaceLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=FACE_MODEL_PATH),
    output_face_blendshapes=True,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=8,
)

class ChairVision:
    def __init__(self, expected_chars):
        self.start_time = time.perf_counter()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cam_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.chair_A_occupied = 0
        self.chair_B_occupied = 0
        
        loaded_data = np.load(f"faces/faces_whole.npz")
        self.known_face_names = list(loaded_data.keys())
        self.known_face_encodings = [loaded_data[name] for name in self.known_face_names]
        self.ai_know_faces = set()
        self.person_chair_history = {}
        self.talking_persons = {}

        self.idsOnChairA = set()
        self.idsOnChairB = set()

        #Gemini
        self.next_track_id = 0
        self.tracked_faces = {}  # Structure: { track_id: {"last_nose": (x,y), "person_id": int, "missing_frames": int} } 
        
        while True:
            selector = ChairZoneSelector(self.cap, expected_chars)
            self.chairBoxes = selector.run()
            if len(self.chairBoxes) > 0:
                break
            print("You have to select at least one box. Retrying...")

        self.face_detector = vision.FaceLandmarker.create_from_options(FACE_OPTIONS)

    def clearHistory(self):
        self.ai_know_faces.clear()
        self.person_chair_history.clear()

    def get_blendshape_score(self, blendshapes, name):
        for b in blendshapes:
            if b.category_name == name:
                return b.score
        return 0.0

    def get_mood(self, blendshapes):
        def bs(name):
            return self.get_blendshape_score(blendshapes, name)

        emotions = {
            "happy": (
                bs("mouthSmileLeft") +
                bs("mouthSmileRight") +
                0.5 * bs("cheekSquintLeft") +
                0.5 * bs("cheekSquintRight")
            ),
            "surprised": (
                bs("jawOpen") +
                bs("eyeWideLeft") +
                bs("eyeWideRight") +
                bs("browInnerUp")
            ),
            "sad": (
                bs("browInnerUp") +
                bs("mouthFrownLeft") +
                bs("mouthFrownRight") +
                0.5 * bs("innerBrowDownLeft") +
                0.5 * bs("innerBrowDownRight")
            ),
            "angry": (
                bs("browDownLeft") +
                bs("browDownRight") +
                bs("noseSneerLeft") +
                bs("noseSneerRight") +
                0.5 * bs("mouthPressLeft") +
                0.5 * bs("mouthPressRight")
            ),
            "disgusted": (
                bs("noseSneerLeft") +
                bs("noseSneerRight") +
                bs("mouthUpperUpLeft") +
                bs("mouthUpperUpRight")
            ),
            "fear": (
                bs("eyeWideLeft") +
                bs("eyeWideRight") +
                bs("browInnerUp") +
                0.5 * bs("jawOpen")
            ),
            "confused": (
                abs(bs("browOuterUpLeft") - bs("browOuterUpRight")) +
                0.5 * bs("mouthShrugUpper")
            ),
            "kiss": (
                bs("mouthPucker") +
                bs("mouthFunnel")
            ),
            "wink": (
                1.2 * max(
                    bs("eyeBlinkLeft") * (1.0 - bs("eyeBlinkRight")),
                    bs("eyeBlinkRight") * (1.0 - bs("eyeBlinkLeft"))
                )
            )
        }

        mood = max(emotions, key=emotions.get)

        if emotions[mood] < 0.9:
            return ""

        return mood
    
    def analyze_frame(self, frame, state):
        height, width, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        timestamp_ms = int((time.perf_counter() - self.start_time) * 1000)
        result = self.face_detector.detect_for_video(mp_image, timestamp_ms)
        chair_memory = ChairMemory()

        idsA = set()
        idsB = set()

        if not result.face_landmarks:
            self.idsOnChairA = idsA
            self.idsOnChairB = idsB
            return chair_memory

        bystanders = len(result.face_landmarks)
        for i, face_landmark in enumerate(result.face_landmarks):
            x_coords = [int(lm.x * width) for lm in face_landmark]
            y_coords = [int(lm.y * height) for lm in face_landmark]
            
            fx1, fx2 = max(0, min(x_coords)), min(width, max(x_coords))
            fy1, fy2 = max(0, min(y_coords)), min(height, max(y_coords))

            face_w, face_h = fx2 - fx1, fy2 - fy1
            p_fx1 = max(0, fx1 - int(face_w * 0.20))
            p_fx2 = min(width, fx2 + int(face_w * 0.20))
            p_fy1 = max(0, fy1 - int(face_h * 0.40))
            p_fy2 = min(height, fy2 + int(face_h * 0.20))

            nose_bridge = face_landmark[168]
            nose_bridgeX, nose_bridgeY = int(nose_bridge.x * width), int(nose_bridge.y * height)
            
            char_letter = "N"
            is_on_chair = False
            for j, box in enumerate(self.chairBoxes):
                x1, y1, x2, y2 = box
                if x1 <= nose_bridgeX <= x2 and y1 <= nose_bridgeY <= y2:
                    if j == 0: char_letter = "A"
                    elif j == 1: char_letter = "B"
                    
                    if char_letter == "A" or char_letter == "B":
                        is_on_chair = True
                        bystanders -= 1
                        break 
            
            face_location = (p_fy1, p_fx2, p_fy2, p_fx1)
            encodings = face_recognition.face_encodings(rgb, known_face_locations=[face_location])
            
            if not encodings:
                continue
                
            current_encoding = encodings[0]
            matches = face_recognition.compare_faces(self.known_face_encodings, current_encoding, tolerance=0.6)
            is_match = True in matches
            
            if is_match:
                person_id = matches.index(True)
                name = self.known_face_names[person_id].split("_")[0] if person_id < len(self.known_face_names) else f"Person_{person_id}"
                print(f"KNOWN FACES: {self.ai_know_faces}\nMatches ID: {person_id} - Name: {name}")
            else:
                if is_on_chair:
                    self.known_face_encodings.append(current_encoding) 
                    person_id = len(self.known_face_encodings) - 1
                    name = f"Person_{person_id}"
                    self.ai_know_faces.add(name)
                    self.person_chair_history[name] = set()
                    print(f"Completly new Person registered! ID: {person_id}")
                    
                    if char_letter == "A":
                        state.total_sits_A += 1
                        chair_memory.completlyNewPersonA += 1
                    elif char_letter == "B":
                        state.total_sits_B += 1
                        chair_memory.completlyNewPersonB += 1
                else:
                    continue 
            if name not in self.person_chair_history:
                self.person_chair_history[name] = set()
            is_real_name = "Person_" not in name

            if is_on_chair:
                if name not in self.ai_know_faces:
                    self.ai_know_faces.add(name)
                    
                    if char_letter == "A":
                        state.total_sits_A += 1
                        if is_real_name: 
                            chair_memory.names_On_A.append(f"{name} first time on Chair A. ")
                        else: 
                            chair_memory.completlyNewPersonA += 1
                    elif char_letter == "B":
                        state.total_sits_B += 1
                        if is_real_name: 
                            chair_memory.names_On_B.append(f"{name} first time on Chair B. ")
                        else: 
                            chair_memory.completlyNewPersonB += 1
                elif is_match: 
                    history = self.person_chair_history[name]
                    
                    if char_letter == "A":
                        if name not in self.idsOnChairA:
                            if "A" in history:
                                if is_real_name: 
                                    chair_memory.names_On_A.append(f"{name} sat down on Chair A again. ")
                                else: 
                                    chair_memory.newPersonwasOnSameChairA += 1
                            elif "B" in history:
                                if is_real_name: 
                                    chair_memory.names_On_B.append(f"{name} swapped from Chair B to Chair A. ")
                                else: 
                                    chair_memory.newPersonWasOnOtherChairA += 1
                        else:
                            if is_real_name: 
                                chair_memory.names_On_A.append(f"{name} hasn't left Chair A. ")
                            else: 
                                chair_memory.samePersonOnA += 1
                            
                    elif char_letter == "B":
                        if name not in self.idsOnChairB:
                            if "B" in history:
                                if is_real_name: 
                                    chair_memory.names_On_B.append(f"{name} sat down on Chair B again. ")
                                else: 
                                    chair_memory.newPersonwasOnSameChairB += 1
                            elif "A" in history:
                                if is_real_name: 
                                    chair_memory.names_On_A.append(f"{name} swapped from Chair A to Chair B. ")
                                else: 
                                    chair_memory.newPersonWasOnOtherChairB += 1
                        else:
                            if is_real_name: 
                                chair_memory.names_On_B.append(f"{name} hasn't left Chair B. ")
                            else: 
                                chair_memory.samePersonOnB += 1

                    print(f"Person {name} recognized => \n{chair_memory}")

                self.person_chair_history[name].add(char_letter)
                if char_letter == "A": 
                    idsA.add(name)
                elif char_letter == "B": 
                    idsB.add(name)
                
            elif char_letter == "N":
                if name in self.ai_know_faces:
                    history = self.person_chair_history[name]
                    if "A" in history and "B" in history:
                        if is_real_name: 
                            chair_memory.names_On_Bystanders.append(f"{name} is a bystander and was on Chair A and on Chair B before. ")
                        else: 
                            chair_memory.knownBystandersBoth += 1
                    elif "A" in history:
                        if is_real_name: 
                            chair_memory.names_On_Bystanders.append(f"{name} is a bystander and was on Chair A before. ")
                        else: 
                            chair_memory.knownBystandersA += 1
                    elif "B" in history:
                        if is_real_name: 
                            chair_memory.names_On_Bystanders.append(f"{name} is a bystander and was on Chair B before. ")
                        else: 
                            chair_memory.knownBystandersB += 1

        self.idsOnChairA = idsA
        self.idsOnChairB = idsB
        return chair_memory

    #generated by Gemmini, commented/adapted by me
    def update_tracking(self, current_noses):
        updated_tracks = {}
        for nose_data in current_noses:
            nx, ny = nose_data["pos"]
            best_track_id = None
            min_dist = 150 #could be a bit high, but wanted to account for freezes or fast movementes
            
            #Check which tracked_face is closest to the current nose-bridge
            for t_id, t_data in self.tracked_faces.items():
                tx, ty = t_data["last_nose"]
                dist = math.hypot(nx - tx, ny - ty)
                if dist < min_dist:
                    min_dist = dist
                    best_track_id = t_id
                    
            #if found set the face to the known person_id and update values
            if best_track_id is not None:
                updated_tracks[best_track_id] = {
                    "last_nose": (nx, ny),
                    "person_id": self.tracked_faces[best_track_id]["person_id"],
                    "missing_frames": 0,
                    "nose_data": nose_data
                }
                del self.tracked_faces[best_track_id] #Found faces get removed, so missing_frames doesn't increase and they dont get skipped later
            #else create new face-object
            else:
                new_id = self.next_track_id
                self.next_track_id += 1
                updated_tracks[new_id] = {
                    "last_nose": (nx, ny),
                    "person_id": None, 
                    "missing_frames": 0,
                    "nose_data": nose_data
                }

        # if an existing face doesn't get detected for 30 frames it gets removed (missing frames gets set to 0 if face detected)
        for t_id, t_data in self.tracked_faces.items():
            if t_data["missing_frames"] < 30:
                t_data["missing_frames"] += 1
                updated_tracks[t_id] = t_data
        
        return updated_tracks

    # this function could be a huge performance hit when more faces are visible
    def analyze_scene_Video(self, frame, state, mood_callback):
        height, width, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        timestamp_ms = int((time.perf_counter() - self.start_time) * 1000)
        result = self.face_detector.detect_for_video(mp_image, timestamp_ms)

        current_noses = []
        
        if result.face_landmarks:
            for i, face_landmark in enumerate(result.face_landmarks):
                for lm in face_landmark:
                    cx, cy = int(lm.x * width), int(lm.y * height)
                    cv2.circle(frame, (cx, cy), 1, (0, 255, 255), -1)
                
                nose = face_landmark[168]
                nx, ny = int(nose.x * width), int(nose.y * height)
                cv2.circle(frame, (nx, ny), 4, (255, 0, 0), -1)
                
                current_noses.append({"pos": (nx, ny), "mp_idx": i, "face_landmark": face_landmark})

        #from gemini + adapted
        self.tracked_faces = self.update_tracking(current_noses) #So not to run face_recognition every frame which would completly destroy framerate (more than it already is)

        
        bystanders = len(current_noses)
        current_A_occupiedNr = 0
        current_B_occupiedNr = 0

        for t_id, t_data in self.tracked_faces.items():
            if t_data["missing_frames"] > 0:
                continue 
                
            nx, ny = t_data["last_nose"]
            lm_idx = t_data["nose_data"]["mp_idx"]
            face_landmark = t_data["nose_data"]["face_landmark"]
            
            #Check on which chair the person sits
            char_letter = None
            for j, box in enumerate(self.chairBoxes):
                x1, y1, x2, y2 = box
                if x1 <= nx <= x2 and y1 <= ny <= y2:
                    bystanders -= 1 
                    if j == 0:
                        char_letter = "A"
                        current_A_occupiedNr += 1
                    elif j == 1:
                        char_letter = "B"
                        current_B_occupiedNr += 1
                    break

            #Thought about if only sitting people get recognized (Could be necessary if performance is too bad)
            #if char_letter is None:
            #    continue
            
            x_coords = [int(lm.x * width) for lm in face_landmark]
            y_coords = [int(lm.y * height) for lm in face_landmark]
            fx1, fx2 = max(0, min(x_coords)), min(width, max(x_coords))
            fy1, fy2 = max(0, min(y_coords)), min(height, max(y_coords))
            
            if t_data["person_id"] is None:                
                face_w, face_h = fx2 - fx1, fy2 - fy1
                p_fx1 = max(0, fx1 - int(face_w * 0.20))
                p_fx2 = min(width, fx2 + int(face_w * 0.20))
                p_fy1 = max(0, fy1 - int(face_h * 0.40))
                p_fy2 = min(height, fy2 + int(face_h * 0.20))
                
                face_location = (p_fy1, p_fx2, p_fy2, p_fx1)
                encodings = face_recognition.face_encodings(rgb, known_face_locations=[face_location])
                
                if encodings:
                    current_encoding = encodings[0]
                    matches = face_recognition.compare_faces(self.known_face_encodings, current_encoding, tolerance=0.6)
                    
                    if True in matches:
                        t_data["person_id"] = matches.index(True)
                    else:
                        self.known_face_encodings.append(current_encoding)
                        t_data["person_id"] = len(self.known_face_encodings) - 1
                        self.person_chair_history[t_data["person_id"]] = set()

            person_id = t_data["person_id"]
            
            if person_id is not None:
                cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (0, 255, 0), 2)
                person_name = self.known_face_names[person_id].split("_")[0] if person_id < len(self.known_face_names) else f"Person_{person_id}"
                if person_name not in self.person_chair_history:
                    self.person_chair_history[person_name] = set()
                

                cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {person_name} (Chair {char_letter})", (fx1, fy1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                #only sitting persons, no bystanders are checkt for talking/mood
                if len(result.face_blendshapes) > lm_idx and char_letter != "N":
                    blend = result.face_blendshapes[lm_idx]
                    
                    #While listening check who is speaking the most
                    if state.listening:
                        jaw_open = self.get_blendshape_score(blend, "jawOpen")
                        mouth_funnel = self.get_blendshape_score(blend, "mouthFunnel")
                        mouth_pucker = self.get_blendshape_score(blend, "mouthPucker")
                        mouth_close = self.get_blendshape_score(blend, "mouthClose")

                        talk_score = (jaw_open * 0.6) + (mouth_funnel * 0.2) + (mouth_pucker * 0.2) - (mouth_close * 0.4)
                        talkChance = max(0.0, min(1.0, talk_score))
                        
                        #TODO: changed talking_persons from id to name, needs testing
                        old_score = self.talking_persons.get(person_name, 0.0)
                        self.talking_persons[person_name] = (old_score * 0.90) + talkChance
                        self.person_chair_history[person_name].add(char_letter)
                        if char_letter == "A" and person_name not in self.idsOnChairA:
                            self.idsOnChairA.add(person_name)
                        if char_letter == "B" and person_name not in self.idsOnChairB:
                            self.idsOnChairB.add(person_name)
                    else:
                        self.talking_persons.clear()

                    #React to moods (Just takes the first person where mood is detected, could change to highest "mood-score", but wouldn't be less random)
                    if not state.block_response and time.time() > state.next_mood_time and mood_callback is not None:
                        mood = self.get_mood(blend)
                        if char_letter == "A":
                            state.person_A_mood = mood
                        elif char_letter == "B":
                            state.person_B_mood = mood

                        if mood != "":
                            state.block_response = True
                            self.ai_know_faces.add(person_name)
                            self.person_chair_history[person_name].add(char_letter)
                            if char_letter == "A" and person_name not in self.idsOnChairA:
                                self.idsOnChairA.add(person_name)
                            if char_letter == "B" and person_name not in self.idsOnChairB:
                                self.idsOnChairB.add(person_name)
                            threading.Thread(target=mood_callback, args=(char_letter, mood, person_name)).start()

        
        if self.talking_persons:
            best_person_name, highest_score = max(self.talking_persons.items(), key=lambda item: item[1])

            #Needs fine-tuning, isn't as reliable as hoped
            if highest_score > 1.1: 
                state.talking_person = best_person_name

        self.chair_A_occupied = current_A_occupiedNr
        self.chair_B_occupied = current_B_occupiedNr

        return self.chair_A_occupied, self.chair_B_occupied, bystanders

    def release(self):
        if self.cap.isOpened():
            self.cap.release()
        try:
            self.face_detector.close()
        except Exception:
            pass


@dataclass
class ChairMemory():
    newPersonWasOnOtherChairA: int = 0
    newPersonWasOnOtherChairB: int = 0
    newPersonwasOnSameChairA: int = 0
    newPersonwasOnSameChairB: int = 0 
    completlyNewPersonA:int = 0
    completlyNewPersonB:int = 0
    samePersonOnA:int = 0
    samePersonOnB:int = 0

    knownBystandersA:int = 0
    knownBystandersB:int = 0
    knownBystandersBoth:int = 0

    names_On_A: list[str] = field(default_factory=list)
    names_On_B: list[str] = field(default_factory=list)
    names_On_Bystanders: list[str] = field(default_factory=list)
