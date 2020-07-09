# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
import sys
import logging
import json
import greengrasssdk
from components import LightControl, SolenoidLock
from localstorage import LocalStorage
import subprocess

# Setup logging to stdout
logger = logging.getLogger(__name__)
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,format=fh_formatter)

# Getting info from env variable. This will be set in Lambda env
STACK_NAME = os.environ['STACK_NAME']
AUDIO_CARD=os.environ["AUDIO_CARD"]
AUDIO_DEVICE=os.environ["AUDIO_DEVICE"]
gg_client = greengrasssdk.client('iot-data')


def auth_run(context, event):
    """ Turn on Activate Light and unlock door.
    After proceeding this method, purchase process will begin by mqtt
    """
    # Activating right
    logger.info("START")

    # Turning on "Green Light(25)" "GPIO.output HIGH"
    LightControl.activate(LightControl.GREEN_LIGHT, deactivate_others=True)
    # Unlock "DOOR KEY(23) "GPIO.output LOW"
    SolenoidLock.unlock()

    local_storage = LocalStorage()
    operation = local_storage.read("qrType")
    if operation == "CUSTOMER":
        cmd = "aplay -D plughw:{},{} pick_instruction.wav".format(AUDIO_CARD,AUDIO_DEVICE)
        subprocess.call(cmd, shell=True)
    elif operation == "REFILL":
        cmd = "aplay -D plughw:{},{} refil_instruction.wav".format(AUDIO_CARD,AUDIO_DEVICE)
        subprocess.call(cmd, shell=True)

    # Debugging to Debug App
    # Value will be changed from "Locked" to "un-Locked"
    payload_info = json.dumps({'type': 'COMPONENT STATE CHANGE', 'data': {
        'title': 'Lock', 'fromValue': 'LOCKED', 'toValue': 'UNLOCKED', 'completedStepIndex': 1}}).encode()
    gg_client.publish(topic='{}/debug'.format(STACK_NAME), payload=payload_info)

    # Debugging to Debug App
    # Value will be changed "from Green Light off to on"
    payload_info = json.dumps({'data': {'title': 'GreenLightstrip', 'fromValue': 'OFF', 'toValue': 'ON'}}).encode()
    gg_client.publish(topic='{}/debug'.format(STACK_NAME), payload=payload_info)

    logger.info("END")
