## Setup and Usage

### Installation

1. Create and activate a Python virtual environment.

2. Install the required dependencies:

    pip install -r requirements.txt

3. Start the application from the command line:

    python app.py

### Command-Line Arguments

The application supports three optional command-line arguments:

- `--mac_os`  
  Enables the macOS-specific window scaling. This option adjusts the window size for the different display resolution on macOS.

- `--xml_logs PATH`  
  Sets the path to the XML files used to train the gesture recognizer. If this argument is not provided, the default dataset path is used.

- `--mediapipe_model PATH`  
  Sets the path to the MediaPipe `hand_landmarker.task` model. If this argument is not provided, the default model path is used.

Example:

    python app.py --macOS

The paths only need to be specified when using custom model or dataset files.

## Drawing

To draw, point the index finger upward toward the camera. Drawing is active while the index finger is extended.

The interaction was found to work best when the thumb is also extended. Extending one or more additional fingers stops the drawing process. The reference point can then be moved without adding new lines.

After completing a stroke and stopping the drawing gesture, letter recognition is triggered automatically. The recognized letter is added to the sentence displayed at the bottom of the application.


## Letter Recognition ##

Each letter must be written in a single continuous stroke. Please refer to the [Single-Stroke Alphabet Rules](#single-stroke-alphabet-rules) for instructions on how to draw each letter.

## Command Gestures


Special gestures can be used to edit the current sentence:

- **Next Word:** Draw the ampersand gesture (`&`) to insert a space and continue with the next word.

  **TODO: Insert screenshot of the Next Word gesture.**

- **End Sentence:** Draw the sentence-ending gesture to add a period.

  **TODO: Insert screenshot of the End Sentence gesture.**

- **Delete Letter:** Draw the delete gesture to remove the previously recognized letter.

  **TODO: Insert screenshot of the Delete Letter gesture.**

- **Restart:** Draw the restart-arrow gesture to clear the complete sentence and start again.

  **TODO: Insert screenshot of the Restart gesture.**

## Toolbar

The toolbar can be controlled by moving the displayed reference point over the desired tool.

The toolbar allows the user to:

- Select different drawing colors
- Activate the eraser
- Clear the complete drawing area
- Increase the pen size using `+`
- Decrease the pen size using `-`


## Single-Stroke Alphabet Rules

All letters must be drawn in one continuous stroke without lifting the finger. The defined starting points and stroke directions should be followed consistently to improve recognition accuracy.

- **A:** Start at the bottom left. Draw diagonally upward to the top, then diagonally downward to the bottom right. Do not draw a crossbar.

- **B:** Start at the top left. Draw straight downward, then move back upward along the same vertical line. From the top, draw the upper curve and continue directly into the lower curve.

- **C:** Start at the top right. Draw counterclockwise around the outside of the shape and finish at the bottom right.

- **D:** Start at the top left. Draw straight downward, then move back upward along the same vertical line. From the top, draw one large outer curve down to the bottom.

- **E:** Start at the top left. Draw the upper horizontal line to the right, then return to the left and draw downward. At the middle, draw the middle horizontal line to the right, return to the vertical line, continue downward, and finally draw the lower horizontal line to the right.

- **F:** Start at the top right. Draw the upper horizontal line to the left, then draw downward. Move upward along the vertical line to the middle and draw the middle horizontal line to the right.

- **G:** Start at the top right. Draw counterclockwise as if drawing a **C**, then continue inward and draw a short horizontal line.

- **H:** Start at the top left. Draw straight downward, then move back upward along the same vertical line. Draw diagonally toward the middle of the right side, continue upward, and finally draw downward along the right side.

- **I:** Start at the top. Draw a straight vertical line downward.

- **J:** Start at the top right. Draw straight downward, then curve toward the left at the bottom.

- **K:** Start at the top left. Draw straight downward, then move upward along the same vertical line to the middle. Draw diagonally toward the top right, return to the middle, and then draw diagonally toward the bottom right.

- **L:** Start at the top left. Draw straight downward, then continue horizontally to the right.

- **M:** Start at the bottom left. Draw straight upward, then diagonally downward toward the center. Draw diagonally upward toward the top right and finally draw straight downward.

- **N:** Start at the bottom left. Draw straight upward, then diagonally downward toward the bottom right. Finally, draw straight upward.

- **O:** Start at the top center. Draw counterclockwise around the shape and return to the starting point.

- **P:** Start at the top left. Draw straight downward, move back upward along the same vertical line, and then draw the upper curve.

- **Q:** Start at the top center. Draw an **O** counterclockwise, return to the starting point, and then continue with a short diagonal tail toward the bottom right.

- **R:** Start at the top left. Draw straight downward, then move back upward along the same vertical line. Draw the upper curve, return to the middle, and finally draw diagonally toward the bottom right.

- **S:** Start at the top right. Curve toward the left, continue through the center toward the right, and finish with a curve toward the bottom left.

- **T:** Start at the top center. Draw straight downward, then move back upward along the same vertical line. Draw the upper horizontal line first toward the left, return to the center, and then continue toward the right.

- **U:** Start at the top left. Draw downward, curve around the bottom, and continue upward along the right side.

- **V:** Start at the top left. Draw diagonally downward toward the bottom center, then diagonally upward toward the top right.

- **W:** Start at the top left. Draw diagonally downward, diagonally upward, diagonally downward again, and finally diagonally upward toward the top right.

- **X:** Start at the top left. Draw diagonally toward the bottom right, then move back to the center. Draw diagonally toward the bottom left, move back through the center, and finally draw diagonally toward the top right.

- **Y:** Start at the top left. Draw diagonally toward the center, then diagonally toward the top right. Move back to the center and finally draw straight downward.

- **Z:** Start at the top left. Draw horizontally toward the top right, then diagonally toward the bottom left, and finally horizontally toward the bottom right.


> **Disclaimer:** ChatGPT was used only to rephrase, translate, and improve the wording and structure of this README. 