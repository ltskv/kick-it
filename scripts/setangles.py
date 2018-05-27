# -*- encoding: UTF-8 -*-
# syntax
# python setangles.py x y

import sys
from naoqi import ALProxy
import time

def main(robotIP,x,y):
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
    angles  = [x,y]
    fractionMaxSpeed  = 0.01
    print motionProxy.setAngles(names, angles, fractionMaxSpeed)

    #time.sleep(3.0)
    #print motionProxy.setStiffnesses("Head", 0.0)


if __name__ == "__main__":
    robotIp = "192.168.0.11"

    #if len(sys.argv) <= 1:
    #    print "Usage python almotion_setangles.py robotIP (optional default: 127.0.0.1)"
    #else:
    #    robotIp = sys.argv[1]
    x=float(sys.argv[1])
    y=float(sys.argv[2])
    main(robotIp,x,y)
