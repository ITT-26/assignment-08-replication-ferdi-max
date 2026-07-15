import sounddevice as sd
from state import ChairState
import onnxruntime
from kokoro_onnx import Kokoro
import speech_recognition as sr
from spellchecker import SpellChecker
import numpy as np
import time
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(script_dir, "models")

class ChairAudio:
    def __init__(self):
        self.spell = SpellChecker(language="en")
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.0
        session = onnxruntime.InferenceSession(
            f"{target_dir}/kokoro-v1.0.fp16-gpu.onnx", 
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.kokoro = Kokoro.from_session(session, f"{target_dir}/voices-v1.0.bin") #Better used with dedicated gpu
        self.cancelToken = False
        print(f"⚠️  Kokoro uses Provider: {session.get_providers()[0]}")

        
        #-------Non GPU Models (Comment in if needed)---------------
        #Tested it and at least for me using the GPU-model with CPU-Provider wasn't much slower than the CPU standard Model
        
        #self.kokoro = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin") #Takes 1-3sec to generate voice, needs good cpu to load fast
        #tried quantized model => 8int not recommended, takes forever (20-40sec)

    def speak(self, text, character, char_letter, state:ChairState) -> bool:
        #Old code for stepwise generation of sentences
        #sentences = re.split(r'(?<=[.!?])\s+', text)
        #sentences = [s.strip() for s in sentences if s.strip()]
        #
        #for sentence in sentences:
        #    state.generate_voice = True
        #    state.speaking = False
        #    state.subtitles = ""

        #    koko_sentence = sentence + " "
        #    samples, sample_rate = self.kokoro.create(koko_sentence, voice=character.value.voice, speed=character.value.speed) 

        #    buffer_duration = 0.1
        #    buffer_samples = np.zeros(int(sample_rate*buffer_duration))
        #    samples = np.concat([samples, buffer_samples])
        #    
        #    state.generate_voice = False
        #    state.speaking = True
        #    state.subtitles = f"Chair {char_letter}: {sentence}"

        #    sd.play(samples, sample_rate)
        #    sd.wait()
        
        #Decided to keep voice generation as a whole instead of single sentences since it sounds more natural
        print(f"Chair {char_letter} says: {text}") 
        state.generate_voice = True
        state.speaking = False
        state.subtitles = ""
        if self.cancelToken:
            self.cancelToken = False
            return False
        
        samples, sample_rate = self.kokoro.create(text, voice=character.value.voice, speed=character.value.speed) 
        buffer_duration = 0.1
        buffer_samples = np.zeros(int(sample_rate*buffer_duration))
        samples = np.concat([samples, buffer_samples])

        state.generate_voice = False
        state.speaking = True
        state.subtitles = f"Chair {char_letter}: {text}"
        sd.play(samples, sample_rate)
        while sd.get_stream().active:
            if self.cancelToken:
                sd.stop()
                self.cancelToken = False
                state.speaking = False
                state.subtitles = ""
                return False
            time.sleep(0.1)
        sd.wait()    
        print("\n----------------------------------------\n")
        state.speaking = False
        state.subtitles = ""
        return True

    def cancel(self, state:ChairState):
        if state.speaking or state.generate_voice or state.listening:
            self.cancelToken = True

    def listen(self, state):
        print("\nChairs are listening...!")
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("Finished recording. Google API is checking...")
                text = self.recognizer.recognize_google(audio, language="en")
                if self.cancelToken:
                    self.cancelToken = False
                    return None
                
                state.request_text = text
                print(f"Understood: '{text}'")
                state.listening = False
                return text
            except sr.UnknownValueError:
                print("Google Speech Recognition error.")
                return None
            except sr.RequestError as e:
                print(f"Connection Error: {e}")
                return None
            except Exception as e:
                print(f"Other Error: {e}")
                return None
        return None
