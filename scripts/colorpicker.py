from __future__ import print_function
from live_recognition import get_frame_nao
import cv2 as cv
import imutils
from naoqi import ALProxy

max_value = 255
max_value_H = 360 // 2
low_H = 0
low_S = 0
low_V = 0
high_H = max_value_H
high_S = max_value
high_V = max_value
window_capture_name = 'Video Capture'
window_detection_name = 'Object Detection'
low_H_name = 'Low H'
low_S_name = 'Low S'
low_V_name = 'Low V'
high_H_name = 'High H'
high_S_name = 'High S'
high_V_name = 'High V'

def do_print():
    print('(%s %s %s): (%s %s %s)' %
          (low_H, low_S, low_V, high_H, high_S, high_V))

def on_low_H_thresh_trackbar(val):
    global low_H
    low_H = min(high_H-1, val)
    cv.setTrackbarPos(low_H_name, window_detection_name, low_H)
    do_print()

def on_high_H_thresh_trackbar(val):
    global high_H
    high_H = max(val, low_H+1)
    cv.setTrackbarPos(high_H_name, window_detection_name, high_H)
    do_print()

def on_low_S_thresh_trackbar(val):
    global low_S
    low_S = min(high_S-1, val)
    cv.setTrackbarPos(low_S_name, window_detection_name, low_S)
    do_print()

def on_high_S_thresh_trackbar(val):
    global high_S
    high_S = max(val, low_S+1)
    cv.setTrackbarPos(high_S_name, window_detection_name, high_S)
    do_print()

def on_low_V_thresh_trackbar(val):
    global low_V
    low_V = min(high_V-1, val)
    cv.setTrackbarPos(low_V_name, window_detection_name, low_V)
    do_print()

def on_high_V_thresh_trackbar(val):
    global high_V
    high_V = max(val, low_V+1)
    cv.setTrackbarPos(high_V_name, window_detection_name, high_V)
    do_print()


cap = cv.VideoCapture(0)

cv.namedWindow(window_capture_name)
cv.namedWindow(window_detection_name)

cv.createTrackbar(
    low_H_name, window_detection_name, low_H,
    max_value_H, on_low_H_thresh_trackbar
)
cv.createTrackbar(
    high_H_name, window_detection_name , high_H, max_value_H,
    on_high_H_thresh_trackbar
)
cv.createTrackbar(
    low_S_name, window_detection_name , low_S, max_value,
    on_low_S_thresh_trackbar
)
cv.createTrackbar(
    high_S_name, window_detection_name , high_S, max_value,
    on_high_S_thresh_trackbar
)
cv.createTrackbar(
    low_V_name, window_detection_name , low_V, max_value,
    on_low_V_thresh_trackbar
)
cv.createTrackbar(
    high_V_name, window_detection_name , high_V, max_value,
    on_high_V_thresh_trackbar
)

vd_proxy = ALProxy('ALVideoDevice', '192.168.0.11', 9559)
cam_subscriber = vd_proxy.subscribeCamera(
    "ball_finder", 0, 1, 13, 20
)

try:
    while True:
        frame = get_frame_nao(vd_proxy, cam_subscriber, 320, 240)

        frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        frame_threshold = cv.inRange(
            frame_HSV, (low_H, low_S, low_V), (high_H, high_S, high_V)
        )

        cv.imshow(window_capture_name, frame)
        cv.imshow(window_detection_name, frame_threshold)

        key = cv.waitKey(1)
        if key == ord('q') or key == 27:
            break
finally:
    vd_proxy.unsubscribe(cam_subscriber)
