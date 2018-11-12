"""Some convenience functions which I leave up to you to explore."""

from __future__ import division

import os
import json
import signal

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


def hsv_mask(hsv, hsv_lower, hsv_upper):
    if hsv_lower[0] > hsv_upper[0]:
        mask_l = cv2.inRange(hsv, tuple(hsv_lower),
                             (180,) + tuple(hsv_upper[1:]))
        mask_u = cv2.inRange(hsv, (0,) + tuple(hsv_lower[1:]),
                             tuple(hsv_upper))
        return cv2.add(mask_l, mask_u)
    else:
        return cv2.inRange(hsv, tuple(hsv_lower), tuple(hsv_upper))


class InterruptDelayed(object):

    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)
        print('SIGINT received. Delaying KeyboardInterrupt.')

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)
