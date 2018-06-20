from __future__ import division

import os
import json

import cv2


HERE = os.path.dirname(os.path.realpath(__file__))


def read_config(cfg_file=os.path.join(HERE, 'nao_defaults.json')):
    with open(cfg_file) as f:
        cfg = json.load(f)
    return cfg


def imresize(frame, width=None, height=None):
    if not width and not height:
        return frame
    if not height:
        sf = width / frame.shape[1]
        sz = (0, 0)
    if not width:
        sf = height / frame.shape[0]
        sz = (0, 0)
    if width and height:
        sf = 0
        sz = (width, height)
    return cv2.resize(frame, sz, fx=sf, fy=sf)


def field_mask(frame, hsv_lower, hsv_upper):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    blurred = cv2.GaussianBlur(hsv, (25, 25), 20)
    thr = cv2.inRange(blurred, tuple(hsv_lower), tuple(hsv_upper))

    # The ususal
    thr = cv2.erode(thr, None, iterations=6)
    thr = cv2.dilate(thr, None, iterations=20)
    return thr
