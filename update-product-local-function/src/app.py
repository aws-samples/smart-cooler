# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3

from logging import getLogger, StreamHandler, DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


def lambda_handler(event, context):
    product = {}
    ddb = boto3.resource('dynamodb')
    table = ddb.Table('this-is-my-smart-cooler-demo-product')
    response = table.scan()
    items = response["Items"]
    
    for item in items:
        product[item.get("product_name")] = float(item.get("price"))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "product" : product
        })
    }