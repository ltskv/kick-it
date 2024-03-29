"""Classes for object detection."""

from __future__ import division
from __future__ import print_function

from collections import deque

import cv2
import numpy as np

from .utils import hsv_mask


class FieldFinder(object):
    """Finds the contour of the field."""

    def __init__(self, hsv_lower, hsv_upper):
        """
        Parameters
        ----------
        hsv_lower, hsv_upper : list
            HSV interval of the field in format [H, S, V]

        """

        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)

    def primary_mask(self, frame):
        """Apply thresholding to the camera image.

        Parameters
        ----------
        frame : array
            OpenCV Image in BGR format

        Returns
        -------
        array
            OpenCV 8-bit 1-channel mask

        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(hsv, (25, 25), 20)
        thr = hsv_mask(blurred, self.hsv_lower, self.hsv_upper)
        thr = cv2.erode(thr, None, iterations=6)
        thr = cv2.dilate(thr, None, iterations=10)
        return thr

    def find(self, frame):
        """Find the contour of the field.

        Parameters
        ----------
        frame : array
            OpenCV Image in BGR format.

        Returns
        -------
        contour or None
            OpenCV contour of the field or None if wasn't found.

        """

        thr = self.primary_mask(frame)
        cnts, _ = cv2.findContours(thr.copy(), cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            return None
        field = max(cnts, key=cv2.contourArea)
        field = cv2.convexHull(field)
        return field

    def draw(self, frame, field):
        """Draw the contour on the image (demo purposes).

        Parameters
        ----------
        frame : array
            OpenCV Image in 3-channel format.
        field : contour
            OpenCV contour of the field as returned by `find`.

        Returns
        -------
        array
            New image with the field contour drawn.

        """
        if field is not None:
            frame = frame.copy()
            cv2.drawContours(frame, (field,), -1, (0, 0, 255), 2)
        return frame

    def mask_it(self, frame, field, inverse=False):
        """Mask out the field or everything else in the image.

        Parameters
        ----------
        frame : array
            OpenCV Image in 3-channel format.
        field : contour
            OpenCV contour of the field as returned by `find`.
        inverse : bool
            If True, mask out the field, if False, everything else.

        Returns
        -------
        array
            New image with masked out something.

        """
        if field is not None:
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.drawContours(mask, (field,), -1, 255, -1)
            if inverse:
                mask = cv2.bitwise_not(mask)
            frame = cv2.bitwise_and(frame, frame, mask=mask)
        return frame


class GoalFinder(object):
    """Find a massive distinctly single-colored goal frame."""

    def __init__(self, hsv_lower, hsv_upper):
        """
        Parameters
        ----------
        hsv_lower, hsv_upper : list
            HSV interval of the field in format [H, S, V]

        """
        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)

    def primary_mask(self, frame):
        """Apply thresholding to the camera image.

        Parameters
        ----------
        frame : array
            OpenCV Image in BGR format

        Returns
        -------
        array
            OpenCV 8-bit 1-channel mask

        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        thr = hsv_mask(hsv, self.hsv_lower, self.hsv_upper)
        thr = cv2.erode(thr, None, iterations=2)
        thr = cv2.dilate(thr, None, iterations=2)
        return thr

    def goal_similarity(self, contour):
        """Calculate the similarity of a contour to the goal.

        Parameters
        ----------
        contour : contour
            An OpenCV contour.

        Returns
        -------
        float
            Similarity (or dissimilarity bcs the smaller the more similar).

        """
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
        """Find the contour of the goal.

        Parameters
        ----------
        frame : array
            An OpenCV image in BGR format.

        Returns
        -------
        contour or None
            An OpenCV contour of the goal or None if wasn't found.

        """
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
        best = min(similarities)
        print('Final goal score:', best)
        print()
        if best > 0.45:
            return None
        # Find the contour with the shape closest to that of the goal
        goal = good_cnts[similarities.index(best)]
        return goal

    def left_right_post(self, contour):
        """Return the pixel coordinates of the L-R goalpost."""
        return contour[...,0].min(), contour[...,0].max()

    def goal_center(self, contour):
        """Return the center of the goal in pixel coordinates."""
        l, r = self.left_right_post(contour)
        print('Left goal post:', l,
              'Right goal post:', r)
        return (l + r) / 2

    def draw(self, frame, goal):
        """Draw the contour on the image (demo purposes).

        Parameters
        ----------
        frame : array
            OpenCV Image in 3-channel format.
        field : contour
            OpenCV contour of the goal as returned by `find`.

        Returns
        -------
        array
            New image with the goal contour drawn.

        """
        if goal is not None:
            frame = frame.copy()
            cv2.drawContours(frame, (goal,), -1, (0, 255, 0), 2)
        return frame


class BallFinder(object):
    """Class to find the red ball."""

    def __init__(self, hsv_lower, hsv_upper, min_radius=0.02):
        """
        Parameters
        ----------
        hsv_lower, hsv_upper : list
            HSV interval of the ball in format [H, S, V].
        min_radius : float
            The minimal radius of the ball as fraction of image height.

        """
        self.hsv_lower = tuple(hsv_lower)
        self.hsv_upper = tuple(hsv_upper)
        self.min_radius = min_radius
        self.history = deque(maxlen=64)

    def primary_mask(self, frame):
        """Apply thresholding to the camera image.

        Parameters
        ----------
        frame : array
            OpenCV Image in BGR format

        Returns
        -------
        array
            OpenCV 8-bit 1-channel mask

        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = hsv_mask(hsv, self.hsv_lower, self.hsv_upper)
        return mask

    def find(self, frame):
        """Find the x, y ball coordinates and the radius.

        Parameters
        ----------
        frame : array
            An OpenCV image in BGR format.

        Returns
        -------
        tuple or None
            ((x, y), radius) or None if wasn't found

        """
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
        """Draw the contour on the image (demo purposes).

        Parameters
        ----------
        frame : array
            OpenCV Image in 3-channel format.
        field : contour
            tuple describing the ball as returned by `find`.

        Returns
        -------
        array
            New image with the field contour drawn.

        """
        if ball is not None:
            frame = frame.copy()
            center, radius = ball
            cv2.circle(frame, center, radius, (255, 255, 0), 1)
        return frame
