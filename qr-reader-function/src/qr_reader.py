# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import logging
import sys
import os
from pyzbar.pyzbar import decode
import cv2
import numpy as np
import time
import requests
import greengrasssdk
from localstorage import LocalStorage
import json
import subprocess


# Getting info from env variable. This will be set in Lambda env
STACK_NAME = os.environ['STACK_NAME']
AMAZON_PAY_SCAN_API = os.environ['AMAZON_PAY_SCAN_API']
IS_SANDBOX =  os.environ["IS_SANDBOX"]
REFILL_QR = os.environ['REFILL_QR']
AUDIO_CARD=os.environ["AUDIO_CARD"]
AUDIO_DEVICE=os.environ["AUDIO_DEVICE"]
VIDEO_DEVICE=os.environ.get("VIDEO_DEVICE", "/dev/video-qr")

# Setup logging to stdout
logger = logging.getLogger(__name__)
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,format=fh_formatter)

gg_client = greengrasssdk.client("iot-data")


def scan_amazon_pay(qr_code):
    logger.info("START")
    response = requests.post(AMAZON_PAY_SCAN_API, json={'sandbox': IS_SANDBOX, 'scanData': qr_code})
    data = json.loads(response.content.decode("utf-8"))
    logging.info(data)
    token_data = {}
    for key, value in data.items():
        logger.info('key:{},value:{}'.format(key,value))
        if key == "chargePermissionId":
            token_data[key] = value
            return token_data
        else:
            token_data["is_error"] = True
    return token_data

def reading_qr_run():
    process_running = True
    status = {}
    local_storage = LocalStorage()

    while process_running:
        # Check order process or refilling process are still proceeded
        logger.info(local_storage.read("is_process"))
        logger.info(local_storage.read("qrType"))
        is_process = local_storage.read("is_process")
        if is_process:
            time.sleep(3)
            continue

        qr_code = local_storage.read("qr_code")
        local_storage.clear("qr_code")
        if qr_code:
            # Checking QR code is for shop to refill things or QR from customer
            if REFILL_QR == qr_code:
                status.update(qrType="REFILL")
                status.update(is_process=True)
                local_storage.write(status)
                # Stopping reading QR code process
                payload_info = json.dumps({"type": "TEXT", "data": {"title": "refill"}}).encode()
                gg_client.publish(topic="refill", queueFullPolicy="AllOrException",payload=payload_info)
                continue

            # Publish messages authentication
            else:
                # Calling scan api for getting token
                pay_result = scan_amazon_pay(str(qr_code))
                status.update(pay_result)
                local_storage.write(status)
                logger.info(local_storage.read("is_error"))

                if local_storage.read("is_error"):
                    cmd = "aplay -D plughw:{},{} cant_read_qr.wav".format(AUDIO_CARD,AUDIO_DEVICE)
                    subprocess.call(cmd, shell=True)
                    status.update(is_error=False, is_process=False, qrType="")
                    local_storage.write(status)
                    continue

                else:
                    status.update(qrType="CUSTOMER")
                    status.update(is_process=True)
                    local_storage.write(status)

                    # Debugging App. This topic does not contain debug. However, this is used for debug application
                    payload_info = json.dumps({'type': 'TEXT', 'data': {
                                                  'title': 'Authentication', 'text': 'Valid authentication QRCode', 'value': qr_code, 'completedStepIndex': 0}}).encode()
                    gg_client.publish(topic='{}/debug'.format(STACK_NAME), payload=payload_info)
                    # Sending publishing message to door open process
                    payload_info = json.dumps({'type': 'TEXT', 'data': {'title': 'authenticate'}}).encode()
                    gg_client.publish(topic='authenticate', queueFullPolicy="AllOrException", payload=payload_info)

        time.sleep(3)

# Start executing the function above
reading_qr_run()
