from __future__ import print_function
from __future__ import division

import cv2
from naoqi import ALProxy
from collections import deque
import numpy as np
import imutils


# Nao configuration
nao_ip = '192.168.0.11'
nao_port = 9559
res = (3, (960, 1280))  # NAOQi code and acutal resolution
fps = 1
cam_id = 0  # 0 := top, 1 := bottom

# Recognition stuff
red_lower = (0, 17, 225)  # HSV coded red interval
red_upper = (42, 255, 255)
min_radius = 10
resized_width = 600


def get_frame(cam_proxy, subscriber):
    result = cam_proxy.getImageRemote(subscriber)
    cam_proxy.releaseImage(subscriber)
    if result == None:
        raise RuntimeError('cannot capture')
    elif result[6] == None:
        raise ValueError('no image data string')
    else:
        # create image
        image = np.zeros((res[1][0], res[1][1], 3), np.uint8)
        values = map(ord, list(result[6]))
        i = 0
        for y in range(res[1][0]):
            for x in range(res[1][1]):
                image.itemset((y, x, 0), values[i + 0])
                image.itemset((y, x, 1), values[i + 1])
                image.itemset((y, x, 2), values[i + 2])
                i += 3
        return image


def find_red_ball(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask = cv2.inRange(hsv, red_lower, red_upper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]

    # only proceed if at least one contour was found
    if len(cnts) == 0:
        return None

    # find the largest contour in the mask, then use
    # it to compute the minimum enclosing circle and
    # centroid
    c = max(cnts, key=cv2.contourArea)
    ((x, y), radius) = cv2.minEnclosingCircle(c)

    if radius < min_radius:
        return None

    M = cv2.moments(c)
    center = (M["m10"] // M["m00"], M["m01"] // M["m00"])
    return center, radius


if __name__ == '__main__':
    vd_proxy = ALProxy('ALVideoDevice', nao_ip, nao_port)
    cam_subscriber = vd_proxy.subscribeCamera(
        "ball_finder", cam_id, res[0], 13, fps
    )
    pts = deque(maxlen=64)
    try:
        while True:
            frame = get_frame(vd_proxy, cam_subscriber)
            # resize the frame, blur it
            frame = imutils.resize(frame, width=resized_width)
            # blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            try:
                center, radius = find_red_ball(frame)
            except TypeError:  # No red ball found and function returned None
                pts.appendleft(None)
                continue

            # draw the circle and centroid on the frame,
            cv2.circle(frame, center, radius, (0, 255, 255), 1)
            cv2.circle(frame, center, 5, (0, 255, 0), -1)
            pts.appendleft(center)

            # loop over the set of tracked points
            for i in range(1, len(pts)):
                # if either of the tracked points are None, ignore them
                if pts[i - 1] is None or pts[i] is None:
                    continue
                # otherwise, compute the thickness of the line and
                # draw the connecting lines
                thickness = int(np.sqrt(64 / float(i + 1)) * 2.5)
                cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

            # show the frame to our screen
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF
    finally:
        vd_proxy.unsubscribe(cam_subscriber)

    print(vd_proxy.unsubscribe(cam_subscriber))
