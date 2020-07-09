# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import numpy as np
import cv2
import os

NUMBER_CAMERAS = os.environ["NUMBER_CAMERAS"]
DEVICES = ['/dev/video-ref1', '/dev/video-ref2']


class _Camera:
        cameras = []
        def __init__(self):
            for id_cam in range(int(NUMBER_CAMERAS)):
                self.cameras.append(cv2.VideoCapture(DEVICES[id_cam]))

        def capture(self, id_cam):
            print(self.cameras[id_cam].get(cv2.CAP_PROP_FRAME_COUNT))
            for i in range(4):
              self.cameras[id_cam].grab()

            ret, frame = self.cameras[id_cam].read()
            return frame

Camera = _Camera()