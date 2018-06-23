from __future__ import division
from __future__ import print_function

from collections import deque

import cv2
import numpy as np


class FieldFinder(object):

    def __init__(self, hsv_lower, hsv_upper):
        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)

    def primary_mask(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(hsv, (25, 25), 20)
        thr = cv2.inRange(blurred, tuple(self.hsv_lower), tuple(self.hsv_upper))
        thr = cv2.erode(thr, None, iterations=6)
        thr = cv2.dilate(thr, None, iterations=10)
        return thr

    def find(self, frame):
        thr = self.primary_mask(frame)
        cnts, _ = cv2.findContours(thr.copy(), cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            return None
        field = max(cnts, key=cv2.contourArea)
        field = cv2.convexHull(field)
        return field

    def draw(self, frame, field):
        if field is not None:
            frame = frame.copy()
            cv2.drawContours(frame, (field,), -1, (0, 0, 255), 2)
        return frame

    def mask_it(self, frame, field, inverse=False):
        if field is not None:
            print(frame.shape)
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.drawContours(mask, (field,), -1, 255, -1)
            if inverse:
                mask = cv2.bitwise_not(mask)
            frame = cv2.bitwise_and(frame, frame, mask=mask)
        return frame


class GoalFinder(object):

    def __init__(self, hsv_lower, hsv_upper):
        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)

    def primary_mask(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        thr = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        thr = cv2.erode(thr, None, iterations=2)
        thr = cv2.dilate(thr, None, iterations=2)
        return thr

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
        print('Goal candidate:', shape_sim, area_sim, final_score)
        return final_score

    def find(self, frame):
        thr = self.primary_mask(frame)
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
        print('Final goal score:', best)
        print()
        if best > 0.45:
            return None
        # Find the contour with the shape closest to that of the goal
        goal = good_cnts[similarities.index(best)]
        return goal

    def left_right_post(self, contour):
        return contour[:,0].min(), contour[:,0].max()

    def goal_center(self, contour):
        l, r = self.left_right_post(contour)
        return (l + r) / 2

    def draw(self, frame, goal):
        if goal is not None:
            frame = frame.copy()
            cv2.drawContours(frame, (goal,), -1, (0, 255, 0), 2)
        return frame


class BallFinder(object):

    def __init__(self, hsv_lower, hsv_upper, min_radius):

        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)
        self.min_radius = min_radius
        self.history = deque(maxlen=64)

    def find(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # construct a mask for the color, then perform  a series of
        # dilations and erosions to remove any small blobs left in the mask ?
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        # mask = cv2.erode(mask, None, iterations=2)
        # mask = cv2.dilate(mask, None, iterations=2)

        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)[-2]

        if len(cnts) == 0:
            print('No red contours')
            self.history.appendleft(None)
            return None

        # find the largest contour in the mask, then use it to compute
        # the minimum enclosing circle and centroid
        c = max(cnts, key=cv2.contourArea)
        (x, y), radius = cv2.minEnclosingCircle(c)

        min_radius_abs = self.min_radius * frame.shape[0]

        if radius < min_radius_abs:
            print('Radius:', radius, 'Min radius:', min_radius_abs)
            self.history.appendleft(None)
            return None

        M = cv2.moments(c)
        try:
            center = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
        except ZeroDivisionError:
            # It's weird but happened yeah
            self.history.append(None)
            return None
        self.history.appendleft((center, int(radius)))
        print('Ball:', center, radius)
        return center, int(radius)

    def draw(self, frame, ball):
        if ball is not None:
            frame = frame.copy()
            center, radius = ball
            cv2.circle(frame, center, radius, (255, 255, 0), 1)
        return frame
            # cv2.circle(frame, center, 5, (0, 255, 0), -1)

        # loop over the set of tracked points
        # for i in range(1, len(self.history)):
            # if either of the tracked points are None, ignore them
            # if self.history[i - 1] is None or self.history[i] is None:
                # continue
            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            # center_now = self.history[i - 1][0]
            # center_prev = self.history[i][0]
            # thickness = int((64 / (i + 1))**0.5 * 2.5)
            # cv2.line(frame, center_now, center_prev, (0, 255, 0), thickness)
