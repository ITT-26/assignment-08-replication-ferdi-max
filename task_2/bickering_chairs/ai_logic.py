import ollama
from characters import Mode
import re
from state import ChairState
from audio_logic import ChairAudio
from chair_vision import ChairMemory, ChairVision

#Notes: 
# - 

MODEL = "llama3.1"
HISTORY_LIMIT = 12 #needs to be a factor of 2 since there are always 2 entries appended at once


class ChairAILogic:
    def __init__(self, audio:ChairAudio):
        self.history_A = []
        self.history_B = []
        self.speaker = audio

    def clear_histories(self):
        self.history_A.clear()
        self.history_B.clear()


    def analyze_face_memory(self, state: ChairState, chairMemory: ChairMemory) -> str:
        memory_notes = []

        # --- BYSTANDER CONTEXT ---
        bystander_context_text = ""
        if state.bystanders > 0:           
            bystander_lines = [f"From the {state.bystanders} bystanders:"]
            if len(chairMemory.names_On_Bystanders) > 0:
                bystander_lines.append("Names and Actions of specific bystanders are:")
                for note in chairMemory.names_On_Bystanders:
                    bystander_lines.append(f"- {note.strip()}")

            unknown_person_count = state.bystanders - len(chairMemory.names_On_Bystanders) - chairMemory.knownBystandersA - chairMemory.knownBystandersB - chairMemory.knownBystandersBoth
            
            if  unknown_person_count > 0:
                bystander_lines.append(f"- {unknown_person_count} are unknown")
            if chairMemory.knownBystandersA > 0:
                bystander_lines.append(f"- {chairMemory.knownBystandersA} other person(s) already sat on Chair A")
            if chairMemory.knownBystandersB > 0:
                bystander_lines.append(f"- {chairMemory.knownBystandersB} other person(s) already sat on Chair B")
            if chairMemory.knownBystandersBoth > 0:
                bystander_lines.append(f"- {chairMemory.knownBystandersBoth} other person(s) already sat on Chair A and Chair B.")
     
            bystander_context_text = "\n".join(bystander_lines)

        # ---CHAIR A CONTEXT ---
        if state.person_A_sitting > 0:
            memory_notes.append(f"From the {state.person_A_sitting} person(s) on Chair A:")
            if len(chairMemory.names_On_A) > 0:
                for note in chairMemory.names_On_A:
                    memory_notes.append(f"- {note.strip()}")

            if chairMemory.completlyNewPersonA > 0:
                memory_notes.append(f"- {chairMemory.completlyNewPersonA} other person(s) is/are completely new and just sat down on Chair A.")
            if chairMemory.newPersonwasOnSameChairA > 0:
                memory_notes.append(f"- {chairMemory.newPersonwasOnSameChairA} other person(s) have already sat on Chair A earlier (returned).")
            if chairMemory.samePersonOnA > 0:
                memory_notes.append(f"- {chairMemory.samePersonOnA} other person(s) still sit on Chair A (haven't moved).")
            if state.mode == Mode.DOUBLE and chairMemory.newPersonWasOnOtherChairA > 0:
                memory_notes.append(f"- {chairMemory.newPersonWasOnOtherChairA} other person(s) swapped to Chair A (previously on Chair B).")


        #---CHAIR B CONTEXT---
        if state.mode == Mode.DOUBLE and state.person_B_sitting > 0:
            memory_notes.append(f"\nFrom the {state.person_B_sitting} person(s) on Chair B:\n")
            if len(chairMemory.names_On_B) > 0:
                for note in chairMemory.names_On_B:
                    memory_notes.append(f"- {note.strip()}")

            if chairMemory.completlyNewPersonB > 0:
                memory_notes.append(f"- {chairMemory.completlyNewPersonB} other person(s) is/are completely new and just sat down on Chair B.")
            if chairMemory.newPersonwasOnSameChairB > 0:
                memory_notes.append(f"- {chairMemory.newPersonwasOnSameChairB} other person(s) have already sat on Chair B earlier (returned).")
            if chairMemory.samePersonOnB > 0:
                memory_notes.append(f"- {chairMemory.samePersonOnB} other person(s) still sit on Chair B (haven't moved).")
            if chairMemory.newPersonWasOnOtherChairB > 0:
                memory_notes.append(f"- {chairMemory.newPersonWasOnOtherChairB} other person(s) swapped to Chair B (previously on Chair A).")


        output_segments = []
        
        if bystander_context_text:
            output_segments.append(bystander_context_text)
            
        if memory_notes:
            chair_text = "\n".join(memory_notes)
            output_segments.append(chair_text)

        return "\n\n".join(output_segments)

    def generate_conversation(self, state:ChairState, chair_memory):
        print("Started generating conversation")

        #Basic general information
        base = f"{state.person_A_sitting} Persons sitting on Chair A."
        if state.mode is Mode.DOUBLE:
            base += f" {state.person_B_sitting} Persons sitting on Chair B."
        crowd_text = f"{state.bystanders} people are standing around watching." if state.bystanders > 0 else "No bystanders are present."

        #Concrete Memory Information (If known person => switched, stayed, bystander, etc.)
        chair_memory_text = self.analyze_face_memory(state, chair_memory)

        env_state = f"{base} {crowd_text} {chair_memory_text}"
        print("ENVIROMENT STATE: \n", env_state)

        # --- CHARACTER A ---
        last_words_from_B = ""
        if state.mode is Mode.DOUBLE and self.history_B:
            last_words_from_B = f"[CHAIR B LAST REPLY]: '{self.history_B[-1]['content']}'\n"

        context_A = f"{last_words_from_B}[ENVIRONMENT CURRENT STATE]: {env_state}"

        system_prompt_A = (
            f"<CORE_IDENTITY>\n"
            f"YOU ARE Chair A, a sentient piece of furniture. This is your absolute identity. "
            f"Always respond from the perspective of a chair! Never confuse yourself with the humans or Chair B.\n"
            f"</CORE_IDENTITY>\n\n"
            f"Personality:\n{state.character_A.value.prompt}"
        )
        
        #print(f"COMPLETE PROMPT A:\n {system_prompt_A}\n{self.history_A}\n{context_A}")
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt_A},
                *self.history_A,
                {"role": "user", "content": context_A}
            ]
        )
        
        text_response = response["message"]["content"]  
        cleaned_A = re.sub(r'\*[^*]+\*', '', text_response)  #Since llama often generates responses like *sigh*, *laugh*, etc.
        
        successful = self.speaker.speak(cleaned_A, state.character_A, "A", state)
        #If canceled remove from history
        if successful:
            #if last_words_from_B != "": 
            self.history_A.append({"role": "user", "content": last_words_from_B})
            self.history_A.append({"role": "assistant", "content": cleaned_A})
        
        #--- CHARACTER B (Double Mode Only) ---
        if state.mode is Mode.DOUBLE:
            context_for_B = (
                f"[ENVIRONMENT CURRENT STATE]: {env_state}\n"
                f"[CHAIR A JUST SAID]: '{cleaned_A}'"
            )
            
            system_prompt_B = (
                f"<CORE_IDENTITY>\n"
                f"YOU ARE Chair B, a sentient piece of furniture. This is your absolute identity. "
                f"You are currently conversing with Chair A. Never confuse Chair A or yourself with the humans!\n"
                f"</CORE_IDENTITY>\n\n"
                f"Personality:\n{state.character_B.value.prompt}"
            )
            #print(f"COMPLETE PROMPT B:\n{system_prompt_B}\n{self.history_B}\n{context_for_B}")
            response_B = ollama.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt_B},
                    *self.history_B,
                    {"role": "user", "content": context_for_B}
                ]
            )
            text_B = response_B["message"]["content"]
            cleaned_B = re.sub(r'\*[^*]+\*', '', text_B)
                
            print(f"Character B: {cleaned_B}")
            self.speaker.speak(cleaned_B, state.character_B, "B", state)
            if successful:
                self.history_B.append({"role": "user", "content": f"[CHAIR A JUST SAID]: '{cleaned_A}'"})
                self.history_B.append({"role": "assistant", "content": cleaned_B})

        if len(self.history_A) > HISTORY_LIMIT: self.history_A = self.history_A[-HISTORY_LIMIT:]
        if len(self.history_B) > HISTORY_LIMIT: self.history_B = self.history_B[-HISTORY_LIMIT:]


    def react_to_mood(self, char_letter, character, mood, state, personId):
        history = self.history_A if char_letter == "A" else self.history_B

        system_prompt = (
            f"<CORE_IDENTITY>\n"
            f"YOU ARE Chair {char_letter}, a sentient piece of furniture. This is your absolute identity. "
            f"Always respond from this perspective! Never confuse yourself with the humans sitting on you.\n"
            f"</CORE_IDENTITY>\n\n"
            f"Personality:\n{character.value.prompt}"
        )

        visuals = (
            f"[VISUAL DETECTION]: The human with the {"id" if ("Person" in personId) else "name"} '{personId}' sitting on you just changed their facial expression. "
            f"Current detected mood: '{mood}'.\n"
        )
        instructions = (
            f"[INSTRUCTION]: React directly to this mood in character. Connect your reaction naturally "
            f"to the ongoing conversation context visible in the history above."
        )
        context = visuals + instructions

        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": context}
            ]
        )

        text_response = response["message"]["content"]  
        cleaned = re.sub(r'\*[^*]+\*', '', text_response)  
        
        print(f"Mood Reaction Chair {char_letter}-{mood}-{personId}-----------------------")
        
        successful = self.speaker.speak(cleaned, character, char_letter, state)
        if successful:
            history.append({"role": "user", "content": visuals})
            history.append({"role": "assistant", "content": cleaned})
        
        if len(self.history_A) > HISTORY_LIMIT: self.history_A = self.history_A[-HISTORY_LIMIT:]
        if len(self.history_B) > HISTORY_LIMIT: self.history_B = self.history_B[-HISTORY_LIMIT:]

    def answer_request(self, state:ChairState, vision:ChairVision):
        request_text = self.speaker.listen(state)
        
        if not request_text:
            return
        
        print(f"{state.talking_person} IS TALKING!!!!!")

        if request_text is None or request_text == "":
            return

        if "chair a" in request_text.lower():
            char_letter = "A"
            character = state.character_A
        elif "chair b" in request_text.lower():
            char_letter = "B"
            character = state.character_B
        else:
            char_letter = "A"
            character = state.character_A

        if state.talking_person != -1:
            vision.ai_know_faces.add(state.talking_person)
            vision.person_chair_history[state.talking_person].add(char_letter)

        history = self.history_A if char_letter == "A" else self.history_B

        system_prompt = (
            f"<CORE_IDENTITY>\n"
            f"YOU ARE Chair {char_letter}, a sentient piece of furniture. This is your absolute identity. "
            f"Always respond from this perspective! Never confuse yourself with the humans sitting on you.\n"
            f"</CORE_IDENTITY>\n\n"
            f"Personality:\n{character.value.prompt}"
        )

        visuals = (
            f"[VISUAL DETECTION]: The human{f" with the {"id" if len(state.talking_person) < 4 else "name"}: {state.talking_person}," if state.talking_person != -1 else ""} who is sitting on you just said the following. "
            f"Human said: '{request_text}'.\n"
        )

        instructions = (
            f"[INSTRUCTION]: React directly to this in character. Connect your reaction naturally "
            f"to the ongoing conversation context visible in the history above."
        )

        context = visuals + instructions

        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": context}
            ]
        )
        text_response = response["message"]["content"]  
        cleaned = re.sub(r'\*[^*]+\*', '', text_response)  
        
        print(f"Request Reaction Chair {char_letter}-{state.talking_person}------------------------")

        state.talking_person = -1
        successfull = self.speaker.speak(cleaned, character, char_letter, state)
        state.request_text = ""
        if successfull:
            history.append({"role": "user", "content": visuals})
            history.append({"role": "assistant", "content": cleaned})
        if len(self.history_A) > HISTORY_LIMIT: self.history_A = self.history_A[-HISTORY_LIMIT:]
        if len(self.history_B) > HISTORY_LIMIT: self.history_B = self.history_B[-HISTORY_LIMIT:]
        
        