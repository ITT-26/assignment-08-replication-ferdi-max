import cv2
import time
from state import ChairState
from characters import Mode

frameCounter = 0

def add_infoText(frame, state:ChairState, vision):
    global frameCounter
    chairBoxes = vision.chairBoxes
    frame_height, frame_width = frame.shape[:2]
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, frame_height - 40), (frame_width, frame_height), (0, 0, 0), -1) 
    cv2.rectangle(overlay, (0, 0), (frame_width, 40), (0, 0, 0), -1) 
    cv2.addWeighted(overlay, 0.4, frame, 1 - 0.4, 0, frame)

    for box in chairBoxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (111, 111, 111), 2)           

    if state.block_response:
        if state.speaking:
            timer_text = "Speaking"
        elif state.generate_voice:
            timer_text = "Generating Voice"
        elif state.listening:
            timer_text = "Listening"
        else:
            timer_text = "Thinking"

        timer_text += "." * (frameCounter // 15)
    elif state.get_Nmbr_of_all_faces() == 0:
        timer_text = "No Person in screen"    
    else:
        timer_text = f"Time till next speech: {max(0, (state.next_comment_time - time.time())):.2f}"
    cv2.putText(frame, timer_text, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    
    character_text_A = f"Character A: {state.character_A.name} | Sit-Counter: {state.total_sits_A:03d}"
    (text_width_A, text_height_A), _ = cv2.getTextSize(character_text_A, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    longer_text_width = text_width_A

    if state.mode is Mode.DOUBLE:            
        character_text_B = f"Character B: {state.character_B.name} | Sit-Counter: {state.total_sits_B:03d}"
        (text_width_B, _), _ = cv2.getTextSize(character_text_B, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        if text_width_B > longer_text_width:
            longer_text_width = text_width_B

        y_pos_B = 20 + text_height_A + 10
        cv2.putText(frame, character_text_B, (frame_width - longer_text_width - 15, y_pos_B), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.putText(frame, character_text_A, (frame_width - longer_text_width - 15, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "Space: Talk to Chairs | Q: Exit", (10, frame_height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if state.request_text != "":
        (t_length, _), _ = cv2.getTextSize(f"Request: {state.request_text}", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.putText(frame, f"Request: {state.request_text}", (frame_width - t_length - 10, frame_height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    #If i let kokoro generate by sentence and not whole response at once =>
    #if state.subtitles:
    #    (text_width, _), _ = cv2.getTextSize(state.subtitles, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    #    x = frame_width // 2 - text_width // 2
    #    y = frame_height - 50
    #    
    #    words = state.subtitles.split()
    #    text_color = (0, 255, 255) if (len(words) > 1 and words[1] == "A:") else (255, 255, 0)
    #    
    #    cv2.putText(frame, state.subtitles, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
    #    cv2.putText(frame, state.subtitles, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)

    calc_subtitle_linebreaks(frame, state, frame_width, frame_height)
    frameCounter = (frameCounter + 1) % 60

    return frame

def calc_subtitle_linebreaks(frame, state, width, height):
    if state.subtitles:
        #All subitles start with either "Chair A:" or "Chair B:"!
        all_words = state.subtitles.split()
        text_color = (0, 255, 255) if (len(all_words) > 1 and all_words[1] == "A:") else (255, 255, 0) #Different color dependant on speaking chair
        
        max_width = width - 320 
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.75
        thickness = 2
        
        lines = []
        current_line = []
        
        #calc the linelength by words, since ai tends to use single words or very short sentences which would lead to too many lines if making a normal split at ". ! ?"
        for word in all_words:
            test_line = " ".join(current_line + [word])
            (text_width, _), _ = cv2.getTextSize(test_line, font, font_scale, thickness)
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                
        if current_line:
            lines.append(' '.join(current_line))
            
        start_y = height - 50
        for i, line in enumerate(reversed(lines)):
            (text_width, text_height), _ = cv2.getTextSize(line, font, font_scale, thickness)
            x = width // 2 - text_width // 2
            y = start_y - (i * (text_height+8))
            
            cv2.putText(frame, line, (x, y), font, font_scale, (0, 0, 0), thickness+1)
            cv2.putText(frame, line, (x, y), font, font_scale, text_color, thickness)