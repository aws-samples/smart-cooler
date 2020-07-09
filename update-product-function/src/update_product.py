# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from inventory import InventoryManager
import sys
import logging

# Setup logging to stdout
logger = logging.getLogger(__name__)
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,format=fh_formatter)

def update_master(event, context):
    logger.info("START")
    inventory_manager = InventoryManager()
    inventory_manager.update_product_info()
    logger.info("END")