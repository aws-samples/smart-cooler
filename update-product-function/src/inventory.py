# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import sqlite3
import requests
import os

DATABASE_PATH = "/smart-cooler/inventory.db"
PRODUCT_MASTER_API = os.environ["PRODUCT_MASTER_UPDATE_API"]

class InventoryManager:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._initialize_database()

    def _get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_database(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        #Creating product table
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS product (
                product_name TEXT NULL,
                price INTEGER NULL
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()

    def update_product_info(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        response = requests.get(PRODUCT_MASTER_API)
        data = json.loads(response.content.decode("utf-8"))

        # Clear all data from product master and then update data
        cursor.execute('delete from product')
        # conn.commit()
        for key, value in data["product"].items():
            cursor.execute('INSERT INTO product VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()

