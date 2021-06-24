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

def main():
    while True:
        sleep(2)
        SetAngle(120)
        sleep(2)
        SetAngle(40)


if __name__ == '__main__':
    main()
