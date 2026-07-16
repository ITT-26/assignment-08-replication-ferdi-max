[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/sPpq67Dc)

# Table of Contents

| Task | Name |
|-|-|
| 00 | [Requirements](#requirements)
| 01 | [Bickering Chairs](#01-bickering-chairs) |
| 02 | [Documentation](#02-documentation) |

## Requirements
- Was tested with **Python 3.12**,  
but should work with any version that supports mediapipe, ollama and the other dependencies
- Graphic-Card with min 5GB of VRAM is strongly recommended (developed on rtx4070/rtx5050, should work with RAM or Mac M-Chips but slower)
- install ollama [Download Ollama](https://ollama.com/download)
- to pull llama3.1 (requires 4.9gb of space and vram, or a Mac M-Chip + RAM),  
open command and run
    ````
    ollama pull llama3.1 
    ````
- Requires CUDA-Toolkit for the kokoro GPU-Model (really a pain to install correctly)
> [!IMPORTANT]    
> Without CUDA-Toolkit the speech-Model could be slower
> CPU-Kokoru model could be faster: https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
> **(need to comment in code in audio_logic.py and move kokoro-v1.0.onnx in models folder!)**  
    
- Other requirements are cmake, visual-studio build-tools (c++)
- if dlib doesn't install (needed for face_recognition) => install setuptools version 70.0 or lower, higher versions didn't work for me
- All in all propably requires 8-10GB of free space
- Could well be that other requirements have limitations, but these were the most prominent ones i had to deal with

## Initializing and starting Virtual Enviroment

### For Windows
Open The Root-Directory (Assignment-08-...) in a Terminal and create + activate the virtual enviroment with (**make sure you use a supported version**):
````
py -m venv venv
venv\Scripts\activate
````
(venv) should now be displayed before your new CommandLine in the Terminal

Next install the requirements:
````
pip install -r requirements.txt
````

### For Mac
The Steps are the same, but the concrete commands different:
````
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````
<hr style="border: 2px solid #444; margin: 60px 0;">


# 01: Bickering Chairs
> [!CAUTION]
> On startup the script will try to download kokoro-v1.0.fp16-gpu.onnx (169MB) and voices-v1.0.bin(27MB)

1. Make sure you have the [Requirements](#requirements) installed!
2. Make sure you curse face_recognition and memory-conditions
3. Start with
    ````
    python task_2/bbickering_chair.py
    ````
    Or with possible arguments:
    ````
    python task_2/bickering_chair.py --character_A GRUMPY --character_B NICE
    ````
    | Argument | Type | Default | Description |
    | :--- | :--- | :--- | :--- |
    | `--character_A` | `str` | NICE | Character of Chair A|
    | `--character_B` | `str` | Random Character (Different to A) | Character of Chair B|

    <br>

    **Possible Characters are**:
    | Argument | Description |
    | :--- | :--- |
    | GRUMPY | A grumpy chair who doesn't like you |
    | NICE | A nice and accommodating chair |
    | LAZY | A lazy, sleepy chair |
    | ZEN | A calm and philosophical chair |
    | ANXIOUS | An anxious and nervous chair |
    | SNOBBISH | This chair is better than you |
    | SUSPECT | Definelty a normal Chair |
    | TOTALYAGOODCHAIR | A nice and kind chair |
    | LONG | Gives very long, chatty responses |
    | SHORT | A chair that gives extra short responses |
    | JESTER | A chaotic and unpredictable trickster chair |
    | DRAMATIC_CHAIR | An over-the-top, intensely dramatic chair |

4. Shortcuts
    | Shortcut | Function |
    | --- | --- |
    | **_A_** | Change Character A|
    | **_B_** | Change Character B|
    | **_SPACE_** | The Model starts listening to voice-input |
    | **_C_** | Cancel current (audio-)output |
    | **_Q_** | Closes the Window |

5. Features:
    - There is a Single and Double Mode depending on drawn boxes or arguments
        - In Double Mode the Characters talk to eachother
    - You can choose between alot of characters (see above)
    - Reacts to events:
        - SitDown, Standup
        - different moods like smiling
    - You can talk to the characters! To adress a specific character just mention "Chair A" or "Chair B" in your request
    - The chairs have memory! Chairs remember who (face_recognition) sat/still sits on which chair or moved/is a bystander now and answer accordingly. They also remember the last few conversations

# 02: Documentation

## Development

Even while presenting this paper in the Journal-Club I mentioned how easy it would be to add a small local LLM with voice-generation to make it more flexible and remove the need for prerecorded phrases which could get old fast.  
As we did not have Distance-Sensors at hand and don't have the requirement of not using video, we decided to implement the detection of sitters and bystanders with computer-vision and mediapipe.  
To accommodate that the area of chairs or benches gets selected manually at the start of the application, this comes with the side-effect, that the setup cannot really get moved while it's running. One could fix this problem by tracking the accelerometer of the notebook (a lot have it by now for drop-protection of the storage) or by analysing frames and moving the bounding rectangles of the chairs/benches accordingly. We decided against this since it is not relevant in the test-setting of the presentation and would exceed the scope.  

The basic structure of Computer-Vision, mediapipe and sitting/bystander-detection is remarkably simple. As is the connection with the local ollama and llama3.1 model.  
At first, llama3 was used, then switched to the 0.2gb larger llama3.1 since it has a much larger context length (128,000 tokens) instead of llama3 (8,192 tokens) and would allow for longer history-awareness of the models/prompts, which is still capped at the last 6 prompts to guarantee a fast inference time.  
At this point llama3.1 got the current state of the frame (how many sitters on A/B and bystanders).  
For voice-output at first a classic text-to-speech package which used the built-in voices of Windows was used. But after some consideration since a local LLM is already used for text-generation, might as well use a model for text-to-speech, for which Kokoro was chosen.
As a result, the Characters.py could also be better defined with fitting voices.

After some testing and thoughts, it became clear, that the interaction with the application still lacked context-awareness and with already using mediapipe, some other improvements could be made. One Idea was the addition of mood-detection via mediapipe blendshapes and having the llama react to it.
Another was adding support for microphone and listening with googles speech recognizer. Now Users can talk to the model directly and it does not just react to the environment.  

But with this feature came the biggest rat-tail of the implementation: **face_recognition**  
The model couldn't recognize people so when someone stands up and comes back, they get treated as new person or the answers generally sound very general. 
So as a result at first normal face-recognition was implemented, saving faces as they were detected. This led to a logic-monster in chair_vision managing all the different possibilities of sit-downs (person still sits, is new, came back, was on other chair before, etc.).  
Then I remembered that for one Task we had to collect a dataset of pictures of us making gestures...So of course, I had to implement it...  
I downloaded three fairly different pictures of each person and ran it through the face-recognition and saved the encodings in a NumPy-file with the persons name (e.g. ferdi_01, ferdi_02, felix_01, etc.).
Then I just had to add it to the already existing known_face_encodings, at least I thought so, but when the name is known it should also be known who sat where, is known, etc. so the code for environment-detection got expanded to account for known_names and differentiates between known_names and just known_persons... This is the short version, the implementation itself was MUCH harder than that, especially to not write complete spaghetti code.
At this point enviroment includes if a person is known, person has name, where person sits, where person did sit, if it stood up, sits down again,.... just so many variables.

But this led to the next problem, what if someone talks to the model or a mood is detected? So, Code was added to get an approximation who talked the most while the application was listening and the person_id which previously was used to refer to known_persons needed to be adapted to work with person_names instead. For this reason, known persons with unknown names got referred to as "Person_XX", which allows to differentiate by checking if the name contains "Person_".

There was a lot more to do, like making sure everything was at least a bit well structured. Like when the application got too big adding a Singleton state, which gets handed to all the different functions. Or the whole current state management, when to allow responses, speaking, etc. plus the display of the state.

At last, it was added that responses could be cancelled, for this we focused on cancelling speech since the generation of text usually only took 0.1-0.5 seconds.

There were more considerations like generating voice by sentence or as a whole, how to handle context, history, environment, a lot of prompt-engineering so the Characters answer accordingly, when the model should react (now it's just when sitting persons changes or mood detected, also how to handle the timer) and so much I probably forgot.

So the downsizing to few states from the original paper makes a lot of sense, but we improved it quite a bit reacting to much more states and additionally using a LLM for answer-generation. Even better results could be achieved using a llm with image-analyzing tools, but since the performance is already an issue it was left out. The addition of face and mood-recognition, as well as listening to requests and having multible characters to choose from already goes far beyond the scope of the original paper.

## Problems
- Getting all the requirements to work took some time, especially getting Kokoru to run on the GPU, since installing the CUDA-Toolkit wasn't enough because of a change in the file-structure all relevant files had to be copied to a different directory manually
- Face recognition sometimes works like a charm, at other times detect the wrong face
- The Performance-Impact of more people couldn't be testet properly
- I underestimated how long the combined inferencetime of all models is (For RTX 4070/i7 10700 during development it was faster than rtx 5050/ryzen 5)
