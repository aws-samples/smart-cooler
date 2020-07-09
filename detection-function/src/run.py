# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import boto3
import json
import io
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import base64
from PIL import Image
from math import floor, ceil

sm = boto3.client('sagemaker-runtime', region_name=os.getenv('REGION_NAME', "us-east-1"))
s3 = boto3.client('s3')

# Sagemaker Endpoint
SAGEMAKER_SSD_ENDPOINT = os.getenv('SAGEMAKER_SSD_ENDPOINT', "detection-endpoint")

# Object Categories
OBJECT_CATEGORIES = os.getenv('OBJECT_CATEGORIES', "['Coca-Cola', 'Frappuccino', 'Pepsi', 'Pure Life']")

# S3 Bucket
IMAGE_S3_BUCKET = os.getenv('IMAGE_S3_BUCKET', "detection-bucket")

# Confidence Thresholds
CONFIDENCE_THRESHOLD_SSD = os.getenv('CONFIDENCE_THRESHOLD_SSD', "0.25")
CONFIDENCE_THRESHOLD_IOU = os.getenv('CONFIDENCE_THRESHOLD_IOU', "0.10")

# Small Box Filter
SMALL_BOX_FILTER_SCORE = os.getenv('SMALL_BOX_FILTER_SCORE', "0.05")

# Enviroment Variables converter for list
OBJECT_CATEGORIES = OBJECT_CATEGORIES.strip("[]").split(", ")

# Enviroment Variables converter for floats
CONFIDENCE_THRESHOLD_SSD = float(CONFIDENCE_THRESHOLD_SSD)
CONFIDENCE_THRESHOLD_IOU = float(CONFIDENCE_THRESHOLD_IOU)
SMALL_BOX_FILTER_SCORE = float(SMALL_BOX_FILTER_SCORE)

def put_s3(image, uuid, id_cam, index):
    IMAGE_S3_FOLDER = 'images'
    print("Uploading pictures to S3.")
    s3.put_object(
        Key='{}/{}_{}_{}.jpg'.format(IMAGE_S3_FOLDER, uuid, id_cam, index), 
        Bucket=IMAGE_S3_BUCKET,
        Body=image,
        ContentType='image/jpeg'
    )
    
    s3.put_object_acl(
        Key='{}/{}_{}_{}.jpg'.format(IMAGE_S3_FOLDER, uuid, id_cam, index),
        Bucket=IMAGE_S3_BUCKET,
        ACL='public-read',
    )
    
def get_object_boundary_box(img, obj_boundaries):
    if (len(obj_boundaries) != 4):
        raise Exception("Sagemaker boundaries are not of size 4")
    # Find size of boundary box 
    img_boundaries = img.getbbox()
    x_size = img_boundaries[2] - img_boundaries[0]
    y_size = img_boundaries[3] - img_boundaries[1]

    # Generate tuple of pixel boundaries using the boundaries generated from model. 
    x_min = floor(x_size * obj_boundaries[0])
    y_min = floor(y_size * obj_boundaries[1])
    x_max = ceil(x_size * obj_boundaries[2])
    y_max = ceil(y_size * obj_boundaries[3])
    return tuple(map(int, [x_min, y_min, x_max, y_max]))

def get_iou(bb1, bb2):
    assert bb1[0] < bb1[2]
    assert bb1[1] < bb1[3]
    assert bb2[0] < bb2[2]
    assert bb2[1] < bb2[3]

    # determine the coordinates of the intersection rectangle
    x_left = max(bb1[0], bb2[0])
    y_top = max(bb1[1], bb2[1])
    x_right = min(bb1[2], bb2[2])
    y_bottom = min(bb1[3], bb2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # The intersection of two axis-aligned bounding boxes is always an
    # axis-aligned bounding box
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # compute the area of both AABBs
    bb1_area = (bb1[2] - bb1[0]) * (bb1[3] - bb1[1])
    bb2_area = (bb2[2] - bb2[0]) * (bb2[3] - bb2[1])
    
    if intersection_area == bb1_area or intersection_area == bb2_area:
        return 1.0
    
    if intersection_area / bb1_area > 0.5  or intersection_area / bb2_area > 0.5:
        return 0.5

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = intersection_area / float(bb1_area + bb2_area - intersection_area)
    assert iou >= 0.0
    assert iou <= 1.0
    return iou

def extract_bounding_boxes(image):
    response = sm.invoke_endpoint(
        EndpointName=SAGEMAKER_SSD_ENDPOINT,
        Body=image,
        ContentType='image/jpeg'
    )

    result = json.loads(response['Body'].read())

    # list for bounding boxes
    bounding_boxes = []

    # Remove bounding boxes above the confidence ssd treshold 
    for prediction in result["prediction"]:
        if prediction[1] >= CONFIDENCE_THRESHOLD_SSD:
            bounding_boxes.append(prediction)

    print("Bounding box quantity before NMS: {}".format(len(bounding_boxes)))
    
    i = 0
    while i < len(bounding_boxes):
        boundbox = bounding_boxes[i]
        len_bounding_boxes = len(bounding_boxes)
        i+=1
            
        if boundbox[5] - boundbox[3] < SMALL_BOX_FILTER_SCORE:
            print("Size Removing, Y small: " + str(boundbox[5] - boundbox[3]))
            bounding_boxes.remove(boundbox)
            i=0
            continue

        if boundbox[4] - boundbox[2] < SMALL_BOX_FILTER_SCORE:
            print("Size Removing, x small: " + str(boundbox[4] - boundbox[2]))
            bounding_boxes.remove(boundbox)
            i=0
            continue   
        
        count = 0
        len_bounding_boxes = len(bounding_boxes)
        while count < len_bounding_boxes:
            
            if boundbox != bounding_boxes[count]:
                check = get_iou(boundbox[2:],bounding_boxes[count][2:])
                if check >= CONFIDENCE_THRESHOLD_IOU:        
                    # Best Score
                    if boundbox[1] < bounding_boxes[count][1]:
                        print("Removing: " + str(boundbox[1]))
                        bounding_boxes.remove(boundbox)

                    else:
                        print("Removing: " + str(bounding_boxes[count][1]))
                        bounding_boxes.remove(bounding_boxes[count])
                
                    print("Item Deleted: {}".format(count))
                    len_bounding_boxes -= 1
            
            # Raise Counter
            count += 1
    
    print("Bounding box quantity after NMS: {}".format(len(bounding_boxes)))

    items = []

    for p in bounding_boxes:
         (klass, score, x0, y0, x1, y1) = p

         if score < CONFIDENCE_THRESHOLD_SSD:
            continue
            
         photo = Image.open(io.BytesIO(image))
         shape = OBJECT_CATEGORIES[int(klass)]
         items.append({
            'product_id': shape,
            'object_detection_score': score,
            'position': get_object_boundary_box(photo, (x0, y0, x1, y1)),
        })
        
    print('extract_bounding_boxes: {}'.format(items))
    
    return items
    
def detect(event, context):
    request = json.loads(event['body'])
    uuid = request['uuid']
    photo = request['img'][0]
    id_cam = request['id_cam']

    photo = base64.b64decode(photo)

    put_s3(photo,uuid,id_cam,'fridge-top-view')
    
    bounding_boxes = extract_bounding_boxes(photo)
    
    return {
        "statusCode": 200,
        "body": json.dumps(bounding_boxes),
    }