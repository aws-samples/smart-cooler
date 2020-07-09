# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import logging
import time
import RPi.GPIO as GPIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info('Purchase/components loaded')

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class _LightControl(object):
    RED_LIGHT, GREEN_LIGHT, WHITE_LIGHT = 'red', 'green', 'white'
    pin_map = {
        RED_LIGHT: 22,
        GREEN_LIGHT: 25,
        WHITE_LIGHT: 24,
    }

    def __init__(self):
        for pin in self.pin_map.values():
            GPIO.setup(pin, GPIO.OUT)

    def activate(self, light_or_lights, deactivate_others=False):
        if not isinstance(light_or_lights, list):
            light_or_lights = [light_or_lights]

        for l in light_or_lights: 
            GPIO.output(self.pin_map[l], GPIO.LOW)

        if deactivate_others:
            other_lights = list(set(self.pin_map.keys()) - set(light_or_lights))
            self.deactivate(other_lights)

    def deactivate(self, light_or_lights):
        if not isinstance(light_or_lights, list):
            light_or_lights = [light_or_lights]

        for l in light_or_lights: 
            GPIO.output(self.pin_map[l], GPIO.HIGH)

    def blink(self, light_or_lights, duration=1, deactivate_others=False):
        self.activate(light_or_lights, deactivate_others=deactivate_others)
        time.sleep(duration)
        self.deactivate(light_or_lights)

class _SolenoidLock(object):
    OPEN, CLOSE = 'open', 'close'
    pin = 23

    def __init__(self):
        GPIO.setup(self.pin, GPIO.OUT)

    def lock(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def unlock(self):
        GPIO.output(self.pin, GPIO.LOW)

LightControl = _LightControl()
SolenoidLock = _SolenoidLock()
