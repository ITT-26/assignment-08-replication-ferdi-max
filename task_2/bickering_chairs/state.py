from dataclasses import dataclass
import time
from characters import Mode, Character
from random import randint
from chair_vision import ChairMemory

@dataclass
class ChairState:
    block_response: bool = False
    speaking: bool = False
    generate_voice: bool = False
    listening: bool = False
    
    request_text: str = ""
    subtitles: str = ""
    next_comment_time: float = 0.0
    next_mood_time: float = 0.0
    
    mode: Mode = Mode.SINGLE
    character_A: Character = None
    character_B: Character = None

    person_A_sitting: int = 0
    person_B_sitting: int = 0
    person_A_mood: str = ""
    person_B_mood: str = ""
    bystanders: int = 0
    talking_person: int = -1

    chair_memory: ChairMemory = None

    total_sits_A: int = 0
    total_sits_B: int = 0
    
    #So values get set when creating objekt, not when compiling
    def __post_init__(self):
        self.next_comment_time = time.time() + 30
        self.next_mood_time = time.time() + 11 #Very first reaction shouldn't be mood, after first normal reaction mood quicker, so model recognizes mood as a reaction to what was said

    def get_Nmbr_of_all_faces(self) -> int:
        return self.person_A_sitting + self.person_B_sitting + self.bystanders

    def set_random_comment_time(self, min_sec=10, max_sec=15):
        self.next_comment_time = time.time() + randint(min_sec, max_sec)

    def set_random_mood_time(self, min_sec=0, max_sec=1):
        self.next_mood_time = time.time() + randint(min_sec, max_sec)