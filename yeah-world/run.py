# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Run a trained model on frames from the camera and play random sounds when
class 0 is detected.
"""
from __future__ import print_function

from sys import argv, stderr, exit
from os import getenv

import numpy as np
from tensorflow import keras

from camera import Camera
from pinet import PiNet
from randomsound import RandomSound

import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
pwm=GPIO.PWM(17, 50)
pwm.start(0)

def SetAngle(angle):
    duty = angle / 18 + 2
    GPIO.output(17, True)
    pwm.ChangeDutyCycle(duty)
    sleep(1)
    GPIO.output(17, False)
    pwm.ChangeDutyCycle(0)


# Smooth out spikes in predictions but increase apparent latency. Decrease on a Pi Zero.
SMOOTH_FACTOR = 0.8

SHOW_UI = getenv("DISPLAY")

if SHOW_UI:
    import pygame


def main():
    if len(argv) != 2 or argv[1] == '--help':
        print("""Usage: run.py MODEL
Use MODEL to classify camera frames and play sounds when class 0 is recognised.""")
        exit(1)

    model_file = argv[1]

    # We use the same MobileNet as during recording to turn images into features
    print('Loading feature extractor')
    extractor = PiNet()

    # Here we load our trained classifier that turns features into categories
    print('Loading classifier')
    classifier = keras.models.load_model(model_file)

    # Initialize the camera and sound systems
    camera = Camera(training_mode=False)
    random_sound = RandomSound()


    numFramesThumbsUp = 0
    numFramesThumbsDown = 0
    isOn = False
    isOff = True


    # Create a preview window so we can see if we are in frame or not
    if SHOW_UI:
        pygame.display.init()
        pygame.display.set_caption('Loading')
        screen = pygame.display.set_mode((512, 512))

    # Smooth the predictions to avoid interruptions to audio
    smoothed = np.ones(classifier.output_shape[1:])
    smoothed /= len(smoothed)

    print('Now running!')
    while True:
        raw_frame = camera.next_frame()

        # Use MobileNet to get the features for this frame
        z = extractor.features(raw_frame)

        # With these features we can predict a 'normal' / 'yeah' class (0 or 1)
        # Keras expects an array of inputs and produces an array of outputs
        classes = classifier.predict(np.array([z]))[0]

        # smooth the outputs - this adds latency but reduces interruptions
        smoothed = smoothed * SMOOTH_FACTOR + classes * (1.0 - SMOOTH_FACTOR)
        selected = np.argmax(smoothed) # The selected class is the one with highest probability

        # Show the class probabilities and selected class
        summary = 'Class %d [%s]' % (selected, ' '.join('%02.0f%%' % (99 * p) for p in smoothed))
        stderr.write('\r' + summary)

        if selected == 0:
            numFramesThumbsUp = 0
            numFramesThumbsDown = 0
        elif selected == 1:
            numFramesThumbsDown = numFramesThumbsDown + 1;
            numFramesThumbsUp = 0;
            if (numFramesThumbsDown > 10 and isOn):
                SetAngle(70)
                isOff = True
                isOn = False
        elif selected == 2:
            numFramesThumbsUp = numFramesThumbsUp + 1;
            numFramesThumbsDown = 0;
            if (numFramesThumbsUp > 10 and isOff):
                SetAngle(120)
                isOff = False
                isOn = True

        # Show the image in a preview window so you can tell if you are in frame
        if SHOW_UI:
            pygame.display.set_caption(summary)
            surface = pygame.surfarray.make_surface(raw_frame)
            screen.blit(pygame.transform.smoothscale(surface, (512, 512)), (0, 0))
            pygame.display.flip()

            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    pygame.quit()
                    break


if __name__ == '__main__':
    main()
