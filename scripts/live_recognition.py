from __future__ import print_function
from __future__ import division

import cv2
import numpy as np
import imutils
from naoqi import ALProxy
from collections import deque


# Nao configuration
nao_ip = '192.168.0.11'
nao_port = 9559
res = (1, (240, 320))  # NAOQi code and acutal resolution
fps = 30
cam_id = 1  # 0 := top, 1 := bottom

# Recognition stuff
red_lower = (0, 185, 170)  # HSV coded red interval
red_upper = (2, 255, 255)
min_radius = 5
resized_width = None  # Maybe we need it maybe don't (None if don't)

def get_frame_nao(cam_proxy, subscriber, width, height):
    result = cam_proxy.getImageRemote(subscriber)
    cam_proxy.releaseImage(subscriber)
    if result == None:
        raise RuntimeError('cannot capture')
    elif result[6] == None:
        raise ValueError('no image data string')
    else:
        return np.frombuffer(result[6], dtype=np.uint8).reshape(
            height, width, 3
        )
        # i = 0
        # for y in range(res[1][0]):
            # for x in range(res[1][1]): # columnwise
                # image.itemset((y, x, 0), values[i + 0])
                # image.itemset((y, x, 1), values[i + 1])
                # image.itemset((y, x, 2), values[i + 2])
                # i += 3
        # return image


def find_colored_ball(frame, hsv_lower, hsv_upper, min_radius):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "green", then perform  a series of
    # dilations and erosions to remove any small blobs left in the mask
    mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    cv2.imshow('ball_mask', mask)
    cv2.waitKey(1)

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

    if radius < min_radius:
        return None

    M = cv2.moments(c)
    center = (int(M["m10"] / M["m00"]),int(M["m01"] // M["m00"]))
    return center, int(radius)


def draw_ball_markers(frame, center, radius, history):
    # draw the enclosing circle and ball's centroid on the frame,
    if center is not None and radius is not None:
        cv2.circle(frame, center, radius, (255, 255, 0), 1)
        cv2.circle(frame, center, 5, (0, 255, 0), -1)

    # loop over the set of tracked points
    for i in range(1, len(history)):
        # if either of the tracked points are None, ignore them
        if history[i - 1] is None or history[i] is None:
            continue
        # otherwise, compute the thickness of the line and
        # draw the connecting lines
        thickness = int(np.sqrt(64 / float(i + 1)) * 2.5)
        cv2.line(frame, history[i - 1], history[i], (0, 255, 0), thickness)

    return frame


def nao_demo():
    cv2.namedWindow('ball_mask')
    cv2.namedWindow('Frame')

    vd_proxy = ALProxy('ALVideoDevice', nao_ip, nao_port)
    cam_subscriber = vd_proxy.subscribeCamera(
        "ball_finder", cam_id, res[0], 13, fps
    )
    history = deque(maxlen=64)

    try:
        while True:
            frame = get_frame_nao(vd_proxy, cam_subscriber, res[1][1],
                                  res[1][0])

            # maybe resize the frame, maybe blur it
            if resized_width is not None:
                frame = imutils.resize(frame, width=resized_width)
                # blurred = cv2.GaussianBlur(frame, (11, 11), 0)

            try:
                center, radius = find_colored_ball(
                    frame, red_lower, red_upper, min_radius
                )
                history.appendleft(center)
                draw_ball_markers(frame, center, radius, history)
            except TypeError:  # No red ball found and function returned None
                history.appendleft(None)
                draw_ball_markers(frame, None, None, history)

            # show the frame to screen
            cv2.imshow("Frame", frame)
            cv2.waitKey(1)

    finally:
        vd_proxy.unsubscribe(cam_subscriber)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    nao_demo()
