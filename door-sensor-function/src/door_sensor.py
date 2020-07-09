# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
import sys
import logging
import json
import time
import greengrasssdk
import RPi.GPIO as GPIO

STACK_NAME = os.environ['STACK_NAME']

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
START = " START "
END = " END "

gg_client = greengrasssdk.client('iot-data')

GPIO.setmode(GPIO.BCM)
DOOR_SENSOR_PIN = 18
GPIO.setup(DOOR_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def run_loop():
    OPEN, CLOSED = 1, 0
    last_status = None
    last_reads = []

    while True: 
        if last_status is None:
            last_status = GPIO.input(DOOR_SENSOR_PIN)
        current_status = GPIO.input(DOOR_SENSOR_PIN)
        logger.info('current status is %s, last status is %s', current_status, last_status)

        last_reads.append(current_status)
        last_reads = last_reads[-10:]

        if len(set(last_reads)) > 1:
            time.sleep(0.05)
            continue

        if last_status == OPEN and current_status == CLOSED:
            logger.info('Door was closed, dispatching message to topic "<STACK_NAME>/close"')
            gg_client.publish(
                topic='{}/close'.format(STACK_NAME),
                payload=json.dumps({}).encode()
            )
            gg_client.publish(
                topic='{}/debug'.format(STACK_NAME),
                payload=json.dumps({
                    'type': 'COMPONENT_STATE_CHANGE',
                    'data':  {
                        'title': 'DoorSensor',
                        'fromValue': 'OPENED',
                        'toValue': 'CLOSED',
                      }
                }).encode()
            )
            # after the door is closed, wait for 5 seconds before reading sensors again
            time.sleep(5)

        last_status = current_status
        time.sleep(1)
        
# when run as lambda, this will be invoked
run_loop()
