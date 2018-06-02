from __future__ import print_function
from __future__ import division

import json
import cv2
import numpy as np
# import imutils
from imagereaders import NaoImageReader, VideoReader
from collections import deque


red_lower = (0, 185, 170)  # HSV coded red interval
red_upper = (2, 255, 255)


class BallFinder(object):

    def __init__(self, hsv_lower, hsv_upper, min_radius, width,
                 viz=False):

        self.hsv_lower = hsv_lower
        self.hsv_upper = hsv_upper
        self.min_radius = min_radius
        self.width = width
        self.history = deque(maxlen=64)
        self.last_center = None
        self.last_radius = None
        self.viz = viz

        if self.viz:
            cv2.namedWindow('ball_mask')
            cv2.namedWindow('Frame')

    def find_colored_ball(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # construct a mask for the color, then perform  a series of
        # dilations and erosions to remove any small blobs left in the mask
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        if self.viz:
            cv2.imshow('ball_mask', mask)

        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)[-2]

        # only proceed if at least one contour was found
        if len(cnts) == 0:
            print('Nothin there')
            return None

        # find the largest contour in the mask, then use it to compute
        # the minimum enclosing circle and centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)

        if radius < self.min_radius:
            return None

        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]),int(M["m01"] // M["m00"]))
        return center, int(radius)

    def next_frame(self, frame):
        # maybe resize the frame, maybe blur it
        # if self.width is not None:
            # frame = imutils.resize(frame, width=self.width)
        try:
            self.last_center, self.last_radius = self.find_colored_ball(frame)
        except TypeError:  # No red ball found and function returned None
            self.last_center, self.last_radius = None, None

        self.history.appendleft(self.last_center)
        self.draw_ball_markers(frame)

        # show the frame to screen
        if self.viz:
            cv2.imshow("Frame", frame)
            return cv2.waitKey(2)

    def draw_ball_markers(self, frame):
        # draw the enclosing circle and ball's centroid on the frame,
        if self.last_center is not None and self.last_radius is not None:
            cv2.circle(frame, self.last_center, self.last_radius,
                       (255, 255, 0), 1)
            cv2.circle(frame, self.last_center, 5, (0, 255, 0), -1)

        # loop over the set of tracked points
        for i in range(1, len(self.history)):
            # if either of the tracked points are None, ignore them
            if self.history[i - 1] is None or self.history[i] is None:
                continue
            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            thickness = int(np.sqrt(64 / float(i + 1)) * 2.5)
            cv2.line(frame, self.history[i - 1], self.history[i],
                     (0, 255, 0), thickness)

        return frame

    def load_hsv_config(self, filename):
        with open(filename) as f:
            hsv = json.load(f)
        self.hsv_lower = tuple(map(hsv.get, ('low_h', 'low_s', 'low_v')))
        self.hsv_upper = tuple(map(hsv.get, ('high_h', 'high_s', 'high_v')))


if __name__ == '__main__':
    # video = NaoImageReader('192.168.0.11')
    video = VideoReader(0, loop=True)
    finder = BallFinder(red_lower, red_upper, 5, None)
    try:
        while True:
            finder.next_frame(video.get_frame())
    finally:
        video.close()
