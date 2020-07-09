# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import sys
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,format=fh_formatter)

DATABASE_PATH = '/smart-cooler/inventory.db'


class InventoryManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH
        self._initialize_database()
        self._initialize_product_info()

    def _get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_database(self):
        conn = self._get_db_connection()
        try:
          cursor = conn.cursor()
          #Creating stock tables
          cursor.execute('''
              CREATE TABLE IF NOT EXISTS snapshots (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  related_order_id TEXT NULL,
                  items text NOT NULL,
                  [timestamp] TIMESTAMP
              );
          ''')

          #Creating product table
          cursor.execute('''
              CREATE TABLE IF NOT EXISTS product (
                  id INTEGER PRIMARY KEY ,
                  product_name TEXT NULL,
                  price INTEGER NULL
              );
          ''')
          
          conn.commit()
          conn.close()
        except sqlite3.Error as e:
          logger.info("conn is closed due to db exception")
          conn.close()

    def _initialize_product_info(self):
        pass


    def get_price(self,product_name):
        conn = self._get_db_connection()
        try:
          cursor = conn.cursor()
          cursor.execute('''SELECT price FROM product WHERE product_name = {}'''.format(product_name))
          result = cursor.fetchall()
          conn.close()
          return result
        except sqlite3.Error as e:
          logger.info("conn is closed due to db exception")
          conn.close()


    def add_snapshot(self, items, related_order_id=None):
        conn = self._get_db_connection()
        try:
          cursor = conn.cursor()
          cursor.execute('''
              INSERT INTO snapshots (timestamp, items, related_order_id)
                  VALUES (?, ?, ?)
          ''', (
              datetime.utcnow(),
              json.dumps(items),
              related_order_id
          ))
          conn.commit()
          conn.close()
        except sqlite3.Error as e:
          logger.info("conn is closed due to db exception")
          conn.close()

    def get_previous_snapshot(self, index=0):
        conn = self._get_db_connection()
        try:
          cursor = conn.cursor()
          cursor.execute('''
              SELECT timestamp, items, related_order_id FROM snapshots 
              ORDER BY id DESC LIMIT 1 OFFSET {}
          '''.format(index))
          result = cursor.fetchone()
          conn.close()
          return {
              'timestamp': result[0],
              'items': json.loads(result[1]),
              'related_order_id': result[2],
          }
          
        except sqlite3.Error as e:
         logger.info("conn is closed due to db exception")
         conn.close()

    def compare_last_snapshots(self):
        before = self.get_previous_snapshot(index=1)['items']
        after = self.get_previous_snapshot(index=0)['items']
        diff = {k: after.get(k, 0) - before.get(k, 0) for k in (list(before) + list(after))}
        return diff
