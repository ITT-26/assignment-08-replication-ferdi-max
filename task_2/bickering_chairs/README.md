[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/sPpq67Dc)


## Requirements
- Was tested with **Python 3.12**,  
but should work with any version that supports mediapipe, ollama and the other dependencies
- Graphic-Card with min 5GB of VRAM is strongly recommended (developed on rtx5050, should work with RAM or Mac M-Chips but slower)
- install ollama [Download Ollama](https://ollama.com/download)
- to pull llama3.1 (requires 4.9gb of space and vram, or a Mac M-Chip + RAM),  
open command and run
    ````
    ollama pull llama3.1 
    ````
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

# Table of Contents

| Task | Name |
|-|-|
| 01 | [Bickering Chairs](#01-bickering-chairs) |
| 02 | [Documentation](#02-documentation) |


# 01: Bickering Chairs
1. Make sure you have the [Dependencies](#requirements) installed!
2. Make sure you curse face_recognition and memory-conditions
3. Start with
    ````
    py -m ./bickering_chair.py
    ````
    Or with possible arguments:
    ````
    py -m fitts_law.py --character_A GRUMPY --character_B NICE
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




        
