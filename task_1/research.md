## Collection of possible Paper ##

Huaizhong Zhu, Chao Deng, and Yuguang Zhu. 2023. </br>
MediaPipe based Gesture Recognition System for English Letters. </br>
In Proceedings of the 2022 11th International Conference on Networks, Communication and Computing (ICNCC '22). </br>
Association for Computing Machinery, New York, NY, USA, 24–30. </br>
https://doi.org/10.1145/3579895.3579900


Takeo Igarashi and Ken Hinckley. 2000. </br>
Speed-dependent automatic zooming for browsing large documents. </br>
In Proceedings of the 13th annual ACM symposium on User interface software and technology (UIST '00). </br>
Association for Computing Machinery, New York, NY, USA, 139–148. </br>
https://doi.org/10.1145/354401.354435


Mall, J., Rani, K., Khatri, D. (2021). </br>
Air Writing: Tracking and Tracing. </br>
In: Singh, S.K., Roy, P., Raman, B., Nagabhushan, P. (eds) Computer Vision and Image Processing. CVIP 2020. </br>
Communications in Computer and Information Science, vol 1378. Springer, Singapore. </br>
https://doi.org/10.1007/978-981-16-1103-2_2


Poh, M.-Z., McDuff, D.J., Picard, R.W. (2010). </br>
Non-contact, automated cardiac pulse measurements using video imaging and blind source separation. </br>
Optics Express, vol 18, no 10, pp. 10762–10774. </br>
https://doi.org/10.1364/OE.18.010762


Takeo Igarashi and John F. Hughes. 2001. </br>
Voice as sound: using non-verbal voice input for interactive control. </br>
In Proceedings of the 14th annual ACM symposium on User interface software and technology (UIST '01). </br>
Association for Computing Machinery, New York, NY, USA, 155–156. </br>
https://doi.org/10.1145/502348.502372


Ann-Sophie L. Schenk, Martin Schymiczek Larangeira de Almeida, Ilknur Sitil, and Xiying Li. 2026. </br>
Bickering Benches: Exploring Playful Interaction in Post-Anthropocentric HRI. </br>
In Companion Proceedings of the 21st ACM/IEEE International Conference on Human-Robot Interaction (HRI Companion '26). </br>
Association for Computing Machinery, New York, NY, USA, 1237–1240. </br>
https://doi.org/10.1145/3776734.3794604

---

## First Approach and Hiccup

At first, we planned to implement and extend the *Bickering Benches* project using computer vision. Ferdi started working on the implementation on the first weekend because Max was busy at that time. However, the project had demanding technical requirements, including a dedicated GPU, many dependencies, and additional C++ build tools. As a result, Max could not run the project reliably on his system.

We therefore decided to keep the existing *Bickering Bench* prototype and focus on making it run reliably. In addition, we chose to implement a second paper so that the work on the first project was not lost and both team members could contribute to the assignment.  
Readme for this process can be found [Here](../task_2/bickering_chairs/README.md#02-documentation)

## Finding a Second Paper

We first explored papers about recognizing American Sign Language (ASL) using MediaPipe hand landmarks. However, after an initial implementation, we found that important parts of the recognition algorithms were not described in enough detail to reproduce them.

We then considered training a Support Vector Machine (SVM) using MediaPipe landmarks. However, finding a suitable ASL dataset was difficult because the required hand orientations were not represented consistently. Since we were not familiar with ASL and creating our own dataset would have required too much time, we decided against this approach.

The idea of recognizing letters through camera input remained interesting to us. During further research, we found the paper *“Air Writing: Tracking and Tracing.”* It was related to our previous ideas, used technologies covered during the semester, and offered several possibilities for additional features. We therefore decided to reproduce and extend its air-writing system.

## Implementation of the Paper

The original paper used an SSD-based hand detector with MobileNetV1. We used MediaPipe instead because it was easier to integrate and we already had experience with it. MediaPipe also provides individual hand landmarks, which allowed us to improve the original interaction.

The paper placed a reference point at the upper center of the detected hand’s bounding box. Drawing was activated when the bounding box had an aspect ratio greater than 1.2. A lower aspect ratio allowed the reference point to be moved without drawing.

We initially implemented this method but found it difficult to use. The user had to open the hand to draw and close it into a fist to stop. While closing the hand, the system often continued drawing because the aspect ratio remained above the threshold for a short time. This created unwanted lines at the end of a stroke.

## Changes to the Interaction

We therefore changed the interaction to use MediaPipe’s hand landmarks. Drawing is now active when only the index finger is extended. When two or more fingers are extended, drawing stops and the reference point can be moved freely.

We also moved the reference point to the tip of the index finger, which provides more direct control and makes switching between drawing and moving easier.

Most of the drawing tools from the paper were kept. However, we changed the size controls so that they adjust both the drawing pen and the eraser.

## Letter Recognition

As an extension, we combined the air-writing system with the **$1 Recognizer**. We recorded our own dataset containing ten samples for each letter. Since the recognizer uses single-stroke gestures, we defined a consistent single-stroke drawing method for every letter.

The completed drawing stroke is passed to the recognizer and compared with the recorded samples. The most similar letter is then displayed by the application.

## Writing Words and Sentences

Finally, we added support for writing words and sentences. Additional gestures allow the user to delete the previous letter, insert a space, restart the current sentence, and finish a sentence by adding a period.

This extends the original drawing application into a system that can recognize letters and create complete words and sentences.

> **Disclaimer:** ChatGPT was used only to rephrase and improve the wording of the research and documentation sections. The research process, decisions, implementation, and described content were created by the authors.
