import json
from collections import deque
import cv2


class BallFinder(object):

    def __init__(self, hsv_lower, hsv_upper, min_radius, viz=False):

        self.hsv_lower = hsv_lower
        self.hsv_upper = hsv_upper
        self.min_radius = min_radius
        self.history = deque(maxlen=64)
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
            self.history.appendleft(None)
            return None

        # find the largest contour in the mask, then use it to compute
        # the minimum enclosing circle and centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)

        if radius < self.min_radius:
            print('Nothin there')
            self.history.appendleft(None)
            return None

        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]),int(M["m01"] // M["m00"]))
        self.history.appendleft((center, int(radius)))
        return center, int(radius)

    def visualize(self, frame):
        if not self.viz:
            raise ValueError(
                'Visualization needs to be enabled when initializing'
            )

        frame = frame.copy()
        if self.history[0] is not None:
            center, radius = self.history[0]
            cv2.circle(frame, center, radius, (255, 255, 0), 1)
            cv2.circle(frame, center, 5, (0, 255, 0), -1)

        # loop over the set of tracked points
        for i in range(1, len(self.history)):
            # if either of the tracked points are None, ignore them
            if self.history[i - 1] is None or self.history[i] is None:
                continue
            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            center_now = self.history[0][0]
            center_prev = self.history[1][0]
            thickness = int((64 / (i + 1))**0.5 * 2.5)
            cv2.line(frame, center_now, center_prev, (0, 255, 0), thickness)
        # show the frame to screen
        cv2.imshow("Frame", frame)
        return cv2.waitKey(1)

    def load_hsv_config(self, filename):
        with open(filename) as f:
            hsv = json.load(f)
        self.hsv_lower = tuple(map(hsv.get, ('low_h', 'low_s', 'low_v')))
        self.hsv_upper = tuple(map(hsv.get, ('high_h', 'high_s', 'high_v')))
