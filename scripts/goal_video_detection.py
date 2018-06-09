# This script recognizes the ball in a given video file
# python ball_tracking.py --video test3.avi

# import the necessary packages
from collections import deque
import numpy as np
import argparse
import imutils
import cv2
from time import sleep
 
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
	help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64,
	help="max buffer size")
args = vars(ap.parse_args())

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
#greenLower = (0, 17, 225)
#greenUpper = (42, 255, 255)


greenLower=(0,184,170)
greenUpper=(2,255,255)

#greenLower = (29, 86, 6)
#greenUpper = (64, 255, 255)
pts = deque(maxlen=args["buffer"])
 
# if a video path was not supplied, grab the reference
# to the webcam
if not args.get("video", False):
	camera = cv2.VideoCapture(0)
 
# otherwise, grab a reference to the video file
else:
	camera = cv2.VideoCapture(args["video"])

# keep looping
while True:
	# grab the current frame
	(grabbed, frame) = camera.read()
 
	# if we are viewing a video and we did not grab a frame,
	# then we have reached the end of the video
	if args.get("video") and not grabbed:
		break
 
	# resize the frame, blur it, and convert it to the HSV
	# color space
#	frame = imutils.resize(frame, width=600)
	# blurred = cv2.GaussianBlur(frame, (11, 11), 0)
#	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
 
	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	
	'''
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
	'''

	# create hsv and do some mask stuff
        frame_HSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
#        frame_test=cv2.cvtColor(frame_HSV,cv2.COLOR_HSV2BGR)
#        frame_gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
       
#	frame_threshold=cv2.inRange(frame_HSV,(0,9,139),(180,81,255))
	frame_threshold=cv2.inRange(frame_HSV,(0,0,182),(180,60,255))

        frame_threshold = cv2.GaussianBlur(frame_threshold,(9,9),3,3)

        erode_element = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        #dilate_element = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
        eroded_mask = cv2.erode(frame_threshold,erode_element)
        #dilated_mask = cv2.dilate(eroded_mask,dilate_element)
        #frame_threshold=eroded_mask
	
	# preparation for edge detection
	res = cv2.bitwise_and(frame,frame, mask=eroded_mask)
	res=cv2.cvtColor(res,cv2.COLOR_BGR2GRAY)


	# use canny edge
	frame_edge=cv2.Canny(res,90,494,apertureSize=3)
	#frame_edge=cv2.Canny(res,0,123,apertureSize=3)
	
	# use hough lines
        lines = cv2.HoughLines(frame_edge,1,1*np.pi/180,80,0,0)

        for rho,theta in lines[0]:
#                print(rho, theta)
                 a = np.cos(theta)
                 b = np.sin(theta)
                 x0 = a*rho
                 y0 = b*rho
                 x1 = int(x0 + 200*(-b))
                 y1 = int(y0 + 200*(a))
                 x2 = int(x0 - 200*(-b))
                 y2 = int(y0 - 200*(a))
                 if (theta>np.pi/180*170 or theta<np.pi/180*10):
		 #if  (theta>np.pi/180*80 and theta<np.pi/180*100):
                         cv2.line(frame,(x1,y1),(x2,y2),(0,0,255),2)


	
	'''
	
		# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)[-2]
	center = None
 
	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
 
		# only proceed if the radius meets a minimum size
		if radius > 10:
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			cv2.circle(frame, (int(x), int(y)), int(radius),
				#(0, 255, 255), 2)
				 (0,255,255),2)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)
 
	# update the points queue
	pts.appendleft(center)

	# loop over the set of tracked points
	for i in xrange(1, len(pts)):
		# if either of the tracked points are None, ignore
		# them
		if pts[i - 1] is None or pts[i] is None:
			continue
 
		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 1.25)
		cv2.line(frame, pts[i - 1], pts[i], (0, 255, 0), thickness)
 	'''
	# show the frame to our screen
	#cv2.imshow("Frame", frame)
	cv2.imshow("Frame_threshold",frame_threshold)
	cv2.imshow("eroded_mask",eroded_mask)
	cv2.imshow("frame edge",frame_edge)
	cv2.imshow("result eroded_mask applied",res)
	cv2.imshow("frame with lines",frame)
	key = cv2.waitKey(1) & 0xFF
 
	sleep(0.05)
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break
 
# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
	

