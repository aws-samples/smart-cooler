# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import requests
import os

AMAZON_PAY_CHARGE_API= os.environ['AMAZON_PAY_CHARGE_API']


class AmazonPay:
    """
    This class deal with Charge function to Amazon pay api
    Attributes:
            sand_box :   When this flag is true, data is send to sand box
            charge_permission_id :  Change permittion id  is got from Amazon pay scan api.
            amount : Amount of mony is charged from customer
            merchant_note : Note info that is displayed in Amazon pay changed notification email
            merchant_store_name : Store name info
            merchant_order_id : This should be used unique number. This can be used order reference numbre
    """
    def __init__(self, sand_box, charge_permission_id, amount, merchant_note, merchant_store_name, merchant_order_id):
        self.sand_box = sand_box
        self.charge_permission_id = charge_permission_id
        self.amount = amount
        self.merchant_note = merchant_note
        self.merchant_store_name = merchant_store_name
        self.merchant_order_id = merchant_order_id

    def proceed_order(self):
        """
        Charge api is run
        """
        payload = {
            "sandbox": self.sand_box,
            "chargePermissionId": self.charge_permission_id,
            "amount": self.amount, "merchantNote": self.merchant_note,
            "merchantStoreName": self.merchant_store_name,
            "merchantOrderId": self.merchant_order_id
        }
        response = requests.post(AMAZON_PAY_CHARGE_API, json=payload)
        data = json.loads(response.content.decode("utf-8"))
        return data
