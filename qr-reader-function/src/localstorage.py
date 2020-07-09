# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import shelve

FILE_PATH = '/smart-cooler/shelve' # Raspberry pi


class LocalStorage:
    def read(self, key):
        try:
            s = shelve.open(FILE_PATH)
            data = s[key]
            s.close()
            return data
        except:
            return {}

    def write(self, data):
        s = shelve.open(FILE_PATH, writeback=True)
        for key, value in data.items():
            s[key] = value
        s.close()
        return True

    def clear(self, key):
        try:
            s = shelve.open(FILE_PATH)
            del s[key]
            return True
        except:
            return False
