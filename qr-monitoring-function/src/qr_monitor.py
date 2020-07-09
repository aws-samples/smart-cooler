# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from pynput.keyboard import Key, Listener
from localstorage import LocalStorage

class Monitor():
    def __init__(self):
        self.qr_data = []
        self.status = {}
        self.local_storage = LocalStorage()

    def on_press(self, key):
        if str(key) != 'Key.enter':
            try:
                self.qr_data.append(key.char[0:1])
            except AttributeError:
                return
        else:
            qr_code = ''.join(self.qr_data)
            self.status.update(qr_code=qr_code)
            self.local_storage.write(self.status)
            self.qr_data.clear()
            return

    def start(self):
        with Listener(on_press=self.on_press) as listener:
            listener.join()

def listen_qr():
    monitor = Monitor()
    monitor.start()

listen_qr()