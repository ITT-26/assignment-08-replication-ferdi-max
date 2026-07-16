import cv2
import os
import ctypes
import time
import threading
from random import sample
import argparse
from characters import Characters, Mode
from ai_logic import ChairAILogic
from chair_vision import ChairVision, ChairMemory
from audio_logic import ChairAudio
from hud_elements import add_infoText
from state import ChairState
import urllib
import sys
#Notes:
# - 

script_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(script_dir, "models")

WINDOW_NAME = "BICKERING CHAIR"
ctypes.windll.shcore.SetProcessDpiAwareness(1)
SCREEN_WIDTH = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_HEIGHT = ctypes.windll.user32.GetSystemMetrics(1)

#Manages Video, state and Characters
class InteractiveChair:
    def __init__(self, characterA: str = None, characterB:str = None):
        expectedChars = 0
        expectedChars = 0
        if characterA is not None: expectedChars += 1
        if characterB is not None: expectedChars += 1

        self.audio = ChairAudio()
        self.ai_logic = ChairAILogic(self.audio)
        self.vision = ChairVision(expectedChars)
        self.state = ChairState()
        self.state.mode = Mode.SINGLE if len(self.vision.chairBoxes) == 1 else Mode.DOUBLE
        self.state.chair_memory = ChairMemory()

        self.setup_character(characterA, characterB)

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        #cv2.resizeWindow(WINDOW_NAME, SCREEN_WIDTH, SCREEN_HEIGHT-20)
        #cv2.moveWindow(WINDOW_NAME,0,0)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def get_random_character(self):
        char_list = list(Characters)
        return sample(char_list, 1)[0]

    def setup_character(self, characterA, characterB):
        print(characterA)
        if characterA is None:
                self.state.character_A = self.get_random_character()
        else:
            try:
                self.state.character_A = Characters[characterA]
            except KeyError:
                self.state.character_B = self.get_random_character()

        if self.state.mode is Mode.DOUBLE:
            if characterB is None:
                self.state.character_B = self.get_random_character()
            else:
                try:
                    self.state.character_B = Characters[characterB]
                except KeyError:
                    self.state.character_B = self.get_random_character()
                    while self.state.character_B == self.state.character_A:
                        self.state.character_B = self.get_random_character()

        print(f"Setup Characters =>\nA: {self.state.character_A} | B: {self.state.character_B}")

    def nextCharacter(self, character_A):
        self.state.set_random_comment_time()
        self.state.set_random_mood_time()

        char_list = list(Characters)
        current_index = char_list.index(character_A)
        next_index = (current_index + 1) % len(char_list)
        return char_list[next_index]

    def listening_worker(self):
        try:
            self.ai_logic.answer_request(
                state=self.state, vision=self.vision
            )
        except Exception as e:
            print(f"Ollama Error: {e}")
        finally:
            self.state.set_random_comment_time(10,15)
            self.state.set_random_mood_time()
            self.state.block_response = False

    def conversation_worker(self, frame):
            #No try/catch since debugging is easier without
            chair_memory = self.vision.analyze_frame(frame, self.state)
            self.ai_logic.generate_conversation(
                self.state, chair_memory
            )
            self.state.set_random_mood_time(1,3)
            self.state.set_random_comment_time()
            self.state.block_response = False

    def mood_worker(self, char_letter, mood, person_id):
        self.state.block_response = True
        character = self.state.character_A if char_letter == "A" else self.state.character_B
        try:
            self.ai_logic.react_to_mood(char_letter, character, mood, self.state, person_id)
        except Exception as e:
            print(f"Ollama Mood Error: {e}")
        finally:
            self.state.set_random_comment_time(7,15)
            self.state.set_random_mood_time(8,12)
            self.state.block_response = False
            

    def handle_keys(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.cleanup()
        elif key == ord('a'):
            self.state.character_A = self.nextCharacter(self.state.character_A)
            self.clearHistory()
        elif key == ord('b'):  
            self.state.character_B = self.nextCharacter(self.state.character_B)
            self.clearHistory()
        elif key == 32 and not self.state.block_response and not self.state.listening:
            self.state.block_response = True
            self.state.listening = True
            threading.Thread(target=self.listening_worker).start()
        elif key == ord("c"):
            self.audio.cancel(self.state)
            
            
    def clearHistory(self):
        self.ai_logic.clear_histories()
        self.vision.clearHistory()
        self.state.total_sits_A = 0
        self.state.total_sits_B = 0

    def run(self):
        print("Run")
        self.is_running = True
        lastNumberofBystanders = 0
        lastNumberofSittersA = 0
        lastNumberofSittersB = 0
        reactCounter = 0
        while self.is_running:
            ret, frame = self.vision.cap.read()
            if not ret:
                time.sleep(0.5)
                continue

            frame = cv2.flip(frame, 1)
            
            person_A_sitting, person_B_sitting, bystanders = self.vision.analyze_scene_Video(
                frame=frame,
                state=self.state,
                mood_callback=self.mood_worker
            )
            if not self.state.block_response:
                self.state.person_A_sitting = person_A_sitting
                self.state.person_B_sitting = person_B_sitting
                self.state.bystanders = bystanders

            frame = add_infoText(
                frame=frame,
                vision=self.vision,
                state= self.state
            )

            cv2.imshow(WINDOW_NAME, frame)

            react_Check = False
            if (lastNumberofSittersA != self.state.person_A_sitting) or (lastNumberofSittersB != self.state.person_B_sitting):
                reactCounter += 1
            else:
                reactCounter = max(0, reactCounter - 1)
            if reactCounter > 40:
                react_Check = True
                lastNumberofBystanders, lastNumberofSittersA, lastNumberofSittersB = self.state.bystanders, self.state.person_A_sitting, self.state.person_B_sitting  
                reactCounter = 0

            if (time.time() > self.state.next_comment_time or react_Check) and not self.state.block_response and not self.state.listening and self.state.get_Nmbr_of_all_faces() > 0:
                self.state.block_response = True
                print(f"AI initiated conversation | due to rection?: {react_Check} | due to timer?: {time.time() > self.state.next_comment_time}")
                threading.Thread(target=self.conversation_worker, args=(frame,)).start()
                    
            self.handle_keys()

    def cleanup(self):
        print("\n....[Cleanup]....") 
        self.is_running = False
        if self.vision.cap.isOpened():
            self.vision.cap.release()
        cv2.destroyAllWindows()
        
        try:
            self.ai_logic.speaker.cancel()
            self.face_detector.close()
        except Exception:
            pass
        
        print("....[Closing]....")
        os._exit(0)


class DownloadHelper():  
    #Just had Gemini generate the basic download-code and adapted it (links, input, filesize, one-line-percentage-display) 
    def download_progress(self, count, block_size, total_size):
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            percent = min(100, percent)
            bar_length = 50
            filled_length = int(bar_length * percent // 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            sys.stdout.write(f"\rProgress: |{bar}| {percent}%")
            sys.stdout.flush()

    def download(self):
        #Tested it and at least for me using the GPU-model with CPU-Provider wasn't much slower than the CPU standard Model, so I didn't add it here since it also has (310mb)
        files_to_download = {
            "kokoro-v1.0.fp16-gpu.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.fp16-gpu.onnx",
            "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
        }
        
        print("-----------[APPLICATION START]-----------------")
        print("The Application relies on the following files to work, please allow the download if prompted!")
        print("Checking for Kokoro-Files...")
        for local_filename, download_url in files_to_download.items():
            destination_path = os.path.join(target_dir, local_filename)
            if not os.path.exists(destination_path):
                if "gpu" in local_filename:
                    file_size = "169MB"
                else:
                    file_size = "27MB"

                answ = input(f"\n⚠️  [INFO] Do you want to allow to download \n'{local_filename}' \ninto \n'{destination_path}'?\n{file_size} is required!\nType y/n: ")
                if answ.lower() != "y":
                    os._exit(0)
                print(f"\ndownloading '{local_filename}'...")
                try:
                    urllib.request.urlretrieve(download_url, destination_path, reporthook=self.download_progress)
                    print(f"\nFinished! Saved at: {destination_path}")
                except Exception as e:
                    print(f"\nError downloading{local_filename}: {e}")
            else:
                print(f"Already Exists: {destination_path}")
        print("\n[Info] Kokoro should be usable!\nIgnore CUDA/onnxRuntime-Error, should just load with CPU, it's slower, but should work\n----------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--character_A", type=str, default=Characters.NICE.name)
    parser.add_argument("--character_B", type=str, default=None)
    args = parser.parse_args()

    DownloadHelper().download()

    chair = InteractiveChair(args.character_A, args.character_B)
    chair.run()