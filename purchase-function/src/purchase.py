# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
import sys
import logging
import json
import base64
import uuid
from cv2 import imwrite
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import requests
import greengrasssdk
from localstorage import LocalStorage
from inventory import InventoryManager
from camera import Camera
from components import LightControl, SolenoidLock
from amazon_pay import AmazonPay
import subprocess

# Logging setting
logger = logging.getLogger(__name__)
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,format=fh_formatter)

STACK_NAME = os.environ['STACK_NAME']
IS_SANDBOX =  os.environ["IS_SANDBOX"]
DETECTION_API_URL = os.environ["DETECTION_API_URL"]
COMPANY_NAME = os.environ["COMPANY_NAME"]
FOOD_CATEGORY = os.environ["FOOD_CATEGORY"]
NUMBER_CAMERAS = os.environ["NUMBER_CAMERAS"]
AUDIO_CARD=os.environ["AUDIO_CARD"]
AUDIO_DEVICE=os.environ["AUDIO_DEVICE"]
TMP_PATH = "/tmp/"


# GG library
gg_client = greengrasssdk.client('iot-data')

# Reading from shelve in order to read chargePermissionId
local_storage = LocalStorage()
inventory_manager = InventoryManager()


def get_image_name(order_id, id_cam, name):
    return '{}_{}_{}.jpg'.format(order_id, id_cam, name)


def copy_image_to_disk(frame, order_id, id_cam, save_path, name):
    filepath = '{}/{}'.format(save_path, get_image_name(order_id, id_cam, name))
    imwrite(filepath, frame)
    return filepath


def take_photo(order_id, id_cam, save_path):
    logger.info("START")
    images = []
    image = Camera.capture(id_cam)
    x = copy_image_to_disk(image, order_id, id_cam, save_path, name='fridge-top-view')
    images.append(x)
    logger.info("END")
    return {'images': images, 'id_cam': id_cam}


def inference_endpoint(order_id, images, id_cam):
    logger.info("START")
    images_base64 = []
    for image in images:
        with open(image, 'rb') as f:
            temp = base64.b64encode(f.read()).decode("utf-8")
            images_base64.append(temp)
    response = requests.post(DETECTION_API_URL,
                             json={'uuid': order_id, 'img': images_base64, 'id_cam': id_cam})
    logger.info("END")
    return {'inference': response, 'id_cam': str(id_cam)}


def transaction(context, event):
    """ purchase transaction

    After closing a refrigerator door, this method is called.
    Taking photos for products left and then detecting what products were taken from picture.
    Afterward, calclating taken product prices and then calling Amazon pay charge API
    """
    logger.info("START")

    # Lock "DOOR KEY(23) "GPIO.output HIGH"
    SolenoidLock.lock()
    # "Green Light" and "Red Light" will be deactivated
    LightControl.deactivate([LightControl.GREEN_LIGHT, LightControl.RED_LIGHT])

    # Debugging App. This topic does not contain debug. However, this is used for debug application
    payload_info = json.dumps({'type': 'COMPONENT_STATE_CHANGE',
                               'data': {'title': 'Lock', 'fromValue': 'UNLOCKED', 'toValue': 'LOCKED','completedStepIndex': 2}}).encode()
    gg_client.publish(topic='{}/debug'.format(STACK_NAME), payload=payload_info)

    payload_info = json.dumps({'type': 'COMPONENT_STATE_CHANGE', ''
                                                                 'data': {'title': 'GreenLightstrip', 'fromValue': 'ON','toValue': 'OFF'}}).encode()
    gg_client.publish(topic='{}/debug'.format(STACK_NAME), payload=payload_info)

    # Get chargePermissionId from shelve
    charge_permission_id = local_storage.read("chargePermissionId")

    # Get Data to save in the name of the /tmp/folder
    date_time = datetime.now().isoformat().replace(':', '_')

    # # Create path to save photo if there is no path
    save_path = TMP_PATH + 'camera/{}'.format(date_time)
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # # Making "Order-ID" this ID will be unique
    order_id = str(uuid.uuid4())
    # # Taking photos. Number of photos is depends on how many number of cameras set
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(take_photo, order_id, id_cam, save_path)
                   for id_cam in range(int(NUMBER_CAMERAS))]
    #     # images keeps "image" and "path that is put "image file"
    images = [r.result() for r in as_completed(futures)]

    # # Debugging App. This topic does not contain debug. However, this is used for debug application
    payload_info = json.dumps({'type': 'TEXT',
                               'data': {'title': 'Camera', 'text': 'Tookpicture, sendingtoinference', 'value': 'null','completedStepIndex': 3}}).encode()
    gg_client.publish(topic='{}/debug'.format(STACK_NAME), payload=payload_info)

    # # Inference Thread
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(inference_endpoint, order_id, image['images'], image['id_cam'])
                   for image in images]
    inferences = [r.result() for r in as_completed(futures)]
    logger.info('Inferences: %s', inferences)
    #
    # # Debugging App. This topic does not contain debug. However, this is used for debug application
    payload_info = json.dumps({'type': 'TEXT',
                               'data': {'title': 'Inference', 'text': 'Inferencerunsuccessfully', 'value': 'null',
                                        'completedStepIndex': 4}}).encode()
    gg_client.publish(topic='{}/debug'.format(STACK_NAME), payload=payload_info)

    # Inference result is stored to "detections array"
    detections = []
    for inference in inferences:
        items = inference['inference'].json()
        for item in items:
            detections.append(item)
    logger.info('Detected: %s', detections)

    detected_inventory = {}
    for item in detections:
        if not item['product_id'] in detected_inventory:
            detected_inventory[item['product_id']] = 1
        else:
            detected_inventory[item['product_id']] += 1
    logger.info('Detected inventory: %s', detected_inventory)

    # This logic is used sqllite3 in Raspberry pi. current stock is registered into database
    inventory_manager.add_snapshot(items=detected_inventory)
    result = inventory_manager.compare_last_snapshots()
    logger.info('Result: %s', result)

    # cal price from diff
    receipt = {'items': [], 'total': 0}
    for item, delta_qty in result.items():
        if delta_qty == 0:
            continue
        delta_qty = delta_qty * -1
        tmp = inventory_manager.get_price(item)
        price = tmp[0][0]
        receipt['items'].append({
            'qty': delta_qty,
            'title': item,
            'product_id': item
        })
        receipt['total'] += price * delta_qty
    total = str(receipt['total'])
    logger.info('Receipt: %s', receipt)

    # Amazon Pay Charge API Calling
    operation = local_storage.read("qrType")
    logger.info(operation)
    if operation == "CUSTOMER":
        amazon_pay = AmazonPay(IS_SANDBOX, charge_permission_id, total, FOOD_CATEGORY, COMPANY_NAME, order_id)
        data = amazon_pay.proceed_order()
        cmd = "aplay -D plughw:{},{} thanks_to_customer.wav".format(AUDIO_CARD,AUDIO_DEVICE)
        subprocess.call(cmd, shell=True)
    elif operation == "REFILL":
        cmd = "aplay -D plughw:{},{} update_stokck.wav".format(AUDIO_CARD,AUDIO_DEVICE)
        subprocess.call(cmd, shell=True)
        
    # Publishing results to debug app
    for inference in inferences:
        image_id = get_image_name(order_id, str(inference['id_cam']), 'fridge-top-view')
        gg_client.publish(
            topic='{}/debug'.format(STACK_NAME), payload=json.dumps({
                'type': 'IMAGE_CANVAS',
                'data': {'uuid': image_id[:-4], 'positions': [
                    {'coord': [
                        r['position'][0],
                        r['position'][1],
                        r['position'][2] - r['position'][0],
                        r['position'][3] - r['position'][1]],
                        'label': r['product_id']}
                    for r in inference['inference'].json()
                ]
                         }
            }).encode()
        )

    # Initializing "chargePermissionId" and QR type info
    local_storage.clear("chargePermissionId")
    local_storage.clear("qrType")
    local_storage.write(dict(is_process=False))

    payload_info = json.dumps({'type': 'TEXT', 'data': {'title': 'qrreader'}}).encode()
    gg_client.publish(topic='qrreader', queueFullPolicy="AllOrException", payload=payload_info)
    logger.info("END")


