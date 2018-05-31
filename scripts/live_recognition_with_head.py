from __future__ import print_function
from __future__ import division

import cv2
import numpy as np
#import imutils
from naoqi import ALProxy
from collections import deque
from imagereaders import NaoImageReader
from live_recognition import BallTracker


# Nao configuration
nao_ip = '192.168.0.10'
nao_port = 9559
#res = (3, (960, 1280))  # NAOQi code and acutal resolution
res=(1,(240,320))
#res=(2,(480,640))

fps = 30
cam_id = 0  # 0 := top, 1 := bottom

# Recognition stuff
red_lower = (0, 185, 170)  # HSV coded red interval
red_upper = (6, 255, 255)
min_radius = 5
resized_width = None  # Maybe we need it maybe don't (None if don't)

current_value = 0


def get_angle():
    robotIP="192.168.0.10"
    PORT = 9559
    motionProxy = ALProxy("ALMotion", robotIP, PORT)
    names=["HeadPitch","HeadYaw"]
    useSensors=False
    angle=motionProxy.getAngles(names,useSensors)
    #print("angle_is"+str(angles))
    return angle


def set_angle(direction):
#def main(robotIP,x,y):
    robotIP="192.168.0.10"
    PORT = 9559
    motionProxy = ALProxy("ALMotion", robotIP, PORT)
    # activiert gelenke
    motionProxy.setStiffnesses("Head", 1.0)
    
    
    #names         = "HeadYaw"
    #useSensors    = False
    
    #commandAngles = motionProxy.getAngles(names, useSensors)

    #type(commandAngles)
    #type(float(commandAngles))
    #current_angle=float(commandAngles)
    #print(current_angle)
    #next_angle=float(commandAngles)-0.2
    #print("next_angle"+str(next_angle))
        #angles  = [0,next_angle]


    
    #print("set_angle")
    # Example showing how to set angles, using a fraction of max speed
    names  = ["HeadYaw", "HeadPitch"]
    #global current_value
    a=get_angle()
    #print(a[0])
#    print(a)
       
    
    #current_value=current_value-0.2
    if direction=="up":
        angles  = [a[1],a[0]-0.2]
    elif direction=="down":
	angles = [a[1], a[0]+0.2]    
    elif direction=="right":
        angles= [a[1]-0.2,a[0]]
    elif direction=="left":
	angles=[a[1]+0.2,a[0]]
    fractionMaxSpeed  = 0.5
    
    motionProxy.setAngles(names, angles, fractionMaxSpeed)


if __name__ == '__main__':
    video = NaoImageReader(nao_ip, port=nao_port, cam_id=cam_id, res=res,
                           fps=fps)
    finder = BallFinder(red_lower, red_upper, 5, None)
    try:
        while True:
            try:
                (x, y), radius = finder.find_colored_ball(video.get_frame())
            except TypeError:
                continue
            if 0<y<100:
                set_angle("up")
            elif 240>y>200:
                set_angle("down")
            if 0<x<100:  # maybe do simultaneous x-y setting
                set_angle("left")
            elif 320>x>220:
                set_angle("right")
    finally:
        video.close()
