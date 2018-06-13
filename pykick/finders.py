from __future__ import division
from __future__ import print_function

import json
from collections import deque

import cv2
import numpy as np


class GoalFinder(object):

    def __init__(self, hsv_lower, hsv_upper):

        self.hsv_lower = hsv_lower
        self.hsv_upper = hsv_upper

    def goal_similarity(self, contour):
        contour = contour.squeeze(axis=1)
        hull = cv2.convexHull(contour).squeeze(axis=1)
        len_h = cv2.arcLength(hull, True)

        # Wild assumption that the goal should lie close to its
        # enclosing convex hull
        shape_sim = np.linalg.norm(contour[:,None] - hull,
                                   axis=2).min(axis=1).sum() / len_h

        # Wild assumption that the area of the goal is rather small
        # compared to its enclosing convex hull
        area_c = cv2.contourArea(contour)
        area_h = cv2.contourArea(hull)

        area_sim = area_c / area_h

        # Final similarity score is just the sum of both
        final_score = shape_sim + area_sim
        print(shape_sim, area_sim, final_score)
        return final_score

    def find_goal_contour(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        print(self.hsv_lower, self.hsv_upper)
        thr = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)

        # The ususal
        thr = cv2.erode(thr, None, iterations=2)
        thr = cv2.dilate(thr, None, iterations=2)
        cnts, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_SIMPLE)
        areas = np.array([cv2.contourArea(cnt) for cnt in cnts])
        # Candidates are at most 6 biggest white areas
        top_x = 6
        if len(areas) > top_x:
            cnt_ind = np.argpartition(areas, -top_x)[-top_x:]
            cnts = [cnts[i] for i in cnt_ind]

        epsilon = [0.01 * cv2.arcLength(cnt, True) for cnt in cnts]

        # Approximate resulting contours with simpler lines
        cnts = [cv2.approxPolyDP(cnt, eps, True)
                for cnt, eps in zip(cnts, epsilon)]

        # Goal needs normally 8 points for perfect approximation
        # But with 6 can also be approximated
        good_cnts = [cnt for cnt in cnts if 6 <= cnt.shape[0] <= 9
                    and not cv2.isContourConvex(cnt)]

        if not good_cnts:
            return None

        similarities = [self.goal_similarity(cnt) for cnt in good_cnts]
        best = min(similarities)
        # if best > 0.4:
            # return None
        # Find the contour with the shape closest to that of the goal
        goal = good_cnts[similarities.index(best)]
        return goal

    def left_right_post(self, contour):
        return contour[:,0].min(), contour[:,0].max()

    def draw(self, frame):
        goal = self.find_goal_contour(frame)
        if goal is not None:
            cv2.drawContours(frame, (goal,), -1, (0, 255, 0), 2)


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

    def draw(self, frame):
        ball = self.find_colored_ball(frame)
        self.history.appendleft(ball)

        if ball is not None:
            center, radius = ball
            cv2.circle(frame, center, radius, (255, 255, 0), 1)
            cv2.circle(frame, center, 5, (0, 255, 0), -1)

        # loop over the set of tracked points
        for i in range(1, len(self.history)):
            # if either of the tracked points are None, ignore them
            if self.history[i - 1] is None or self.history[i] is None:
                continue
            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            center_now = self.history[i - 1][0]
            center_prev = self.history[i][0]
            thickness = int((64 / (i + 1))**0.5 * 2.5)
            cv2.line(frame, center_now, center_prev, (0, 255, 0), thickness)

    def load_hsv_config(self, filename):
        with open(filename) as f:
            hsv = json.load(f)
        self.hsv_lower = tuple(map(hsv.get, ('low_h', 'low_s', 'low_v')))
        self.hsv_upper = tuple(map(hsv.get, ('high_h', 'high_s', 'high_v')))
