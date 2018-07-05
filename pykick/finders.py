from __future__ import division
from __future__ import print_function

from collections import deque

import cv2
import numpy as np

from .utils import hsv_mask, contour_center


class FieldFinder(object):

    def __init__(self, hsv_lower, hsv_upper):
        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)

    def primary_mask(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(hsv, (25, 25), 20)
        thr = hsv_mask(blurred, self.hsv_lower, self.hsv_upper)
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
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.drawContours(mask, (field,), -1, 255, -1)
            if inverse:
                mask = cv2.bitwise_not(mask)
            frame = cv2.bitwise_and(frame, frame, mask=mask)
        return frame


class GoalFinder(object):

    def __init__(self, hsv_lower, hsv_upper, goal_thr=0.45):
        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)
        self.goal_thr = goal_thr
        self.last_detection = []

    def primary_mask(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        thr = hsv_mask(hsv, self.hsv_lower, self.hsv_upper)
        thr = cv2.erode(thr, None, iterations=2)
        thr = cv2.dilate(thr, None, iterations=2)
        return thr

    def goal_similarity(self, contour):
        hull = cv2.convexHull(contour).squeeze()
        len_h = cv2.arcLength(hull, True)

        # Supporting points of goal contour should lie close to its
        # enclosing convex hull
        distances = np.array([[np.sqrt(np.sum(point**2)) for point in node]
                              for node in contour - hull])
        min_dist = np.array([d.min() for d in distances])
        shape_sim = min_dist.sum() / len_h

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
        self.last_detection = []
        thr = self.primary_mask(frame)
        cnts, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
        cnts.sort(key=cv2.contourArea, reverse=True)
        top_x = 6
        cnts = cnts[:top_x]

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
        self.last_detection = list(zip(good_cnts, similarities))
        best = min(similarities)
        print('Final goal score:', best)
        print()
        if best > self.goal_thr:
            return None
        # Find the contour with the shape closest to that of the goal
        goal = good_cnts[similarities.index(best)]
        return goal

    def left_right_post(self, contour):
        return contour[...,0].min(), contour[...,0].max()

    def goal_center(self, contour):
        l, r = self.left_right_post(contour)
        print('Left goal post:', l,
              'Right goal post:', r)
        return (l + r) / 2

    def draw(self, frame, goal):
        frame = frame.copy()
        cv2.putText(frame,
                    'Upper threshold: ' + '%.2f' % self.goal_thr, (10, 50),
                    cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0))
        if self.last_detection:
            cnts = sorted(self.last_detection,
                          key=lambda x: x[1])
            if cnts[0][1] < self.goal_thr:
                goal, score = cnts[0]
                cnts = cnts[1:]
            for cnt, sim in cnts[1:]:
                print(sim)
                cv2.drawContours(frame, (cnt,), -1, (0, 0, 255), 1)
                cv2.putText(frame, '%.2f' % sim, contour_center(cnt),
                            cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255))

        if goal is not None:
            print(goal)
            cv2.drawContours(frame, (goal,), -1, (0, 255, 0), 2)
            cv2.putText(frame, '%.2f' % score, contour_center(goal),
                        cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0))
        return frame


class BallFinder(object):

    def __init__(self, hsv_lower, hsv_upper, min_radius=0.02):

        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)
        self.min_radius = min_radius
        self.history = deque(maxlen=64)

    def primary_mask(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = hsv_mask(hsv, self.hsv_lower, self.hsv_upper)
        return mask

    def find(self, frame):
        mask = self.primary_mask(frame)
        cnts, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)

        if len(cnts) == 0:
            print('No red contours')
            self.history.appendleft(None)
            return None

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
        frame = frame.copy()
        if ball is not None:
            center, radius = ball
            cv2.circle(frame, center, radius, (255, 255, 0), 2)
        for i in range(1, len(self.history)):
            if self.history[i - 1] is None or self.history[i] is None:
                continue
            center_now = self.history[i - 1][0]
            center_prev = self.history[i][0]
            thickness = int((64 / (i + 1))**0.5 * 1.25)
            cv2.line(frame, center_now, center_prev, (0, 0, 255), thickness)
        return frame
