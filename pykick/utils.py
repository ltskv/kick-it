from __future__ import division

import os
import json

import cv2
import numpy as np


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


def hsv_mask(hsv, hsv_lower, hsv_upper):
    if hsv_lower[0] > hsv_upper[0]:
        mask_l = cv2.inRange(hsv, tuple(hsv_lower),
                             tuple([180] + hsv_upper[1:]))
        mask_u = cv2.inRange(hsv, tuple([0] + hsv_lower[1:]),
                             tuple(hsv_upper))
        return cv2.add(mask_l, mask_u)
    else:
        return cv2.inRange(hsv, tuple(hsv_lower), tuple(hsv_upper))
