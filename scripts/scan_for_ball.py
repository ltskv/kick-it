# -*- encoding: UTF-8 -*-
# syntax
# python setangles.py x y

import sys
from naoqi import ALProxy
import time

def main(robotIP):
    PORT = 9559

    try:
        motionProxy = ALProxy("ALMotion", robotIP, PORT)
    except Exception,e:
        print "Could not create proxy to ALMotion"
        print "Error was: ",e
        sys.exit(1)

    # activiert gelenke
    motionProxy.setStiffnesses("Head", 1.0)

    # Example showing how to set angles, using a fraction of max speed
    names  = ["HeadYaw", "HeadPitch"]
    
    # go into left direction        
    i=0
    while i<2:
       angles = [i,0]
       fractionMaxSpeed =0.5    
       motionProxy.setAngles(names, angles, fractionMaxSpeed)
       i=float(i)+3.14/4
       time.sleep(0.3)

    # go back to middle position
    angles = [0,0]
    fractionMaxSpeed =0.5    
    motionProxy.setAngles(names, angles, fractionMaxSpeed)
    print "head set back"
    time.sleep(0.3)

    # go into the right direction
    i=0
    while i > -2:
       angles = [i,0]
       fractionMaxSpeed =0.5    
       motionProxy.setAngles(names, angles, fractionMaxSpeed)
       i=i-3.14/4
       time.sleep(0.3)

    # go back to middle position
    angles = [0,0]
    fractionMaxSpeed =0.5    
    motionProxy.setAngles(names, angles, fractionMaxSpeed)
    print "head set back"
    time.sleep(1)

if __name__ == "__main__":
    robotIp = "192.168.0.11"

    main(robotIp)
