import time
import argparse
from naoqi import ALProxy
from math import radians


def main(robotIP, PORT=9559):
    motionProxy = ALProxy("ALMotion", robotIP, PORT)

    motionProxy.setStiffnesses("Head", 1.0)
    motionProxy.setStiffnesses("LShoulderRoll",0.9)
    motionProxy.setStiffnesses("LHipPitch",0.9)
    # Example showing how to set angles, using a fraction of max speed
    #names  = ["HeadYaw", "HeadPitch"]
    #angles  = [0.2, -0.2]
    fractionMaxSpeed = 0.5
    names=["RShoulderRoll","RElbowRoll"]
    angles=[radians(-76),0]
    motionProxy.setAngles(names,angles,fractionMaxSpeed)

    time.sleep(3)

    fractionMaxSpeed  = 0.01
    motionProxy.setStiffnesses("RAnkleRoll",0.9)
    names=["LHipRoll","RHipRoll","LHipPitch","RAnkleRoll"]
    angles=[radians(-10),radians(-10),radians(-15),radians(-5)]
    motionProxy.setAngles(names, angles, fractionMaxSpeed)

    #motionProxy.waitUntilMoveIsFinished()
    time.sleep(6)
    
    motionProxy.setStiffnesses("RAnklePitch",0.9)
    names=["RKneePitch","RHipPitch","LAnklePitch"]
    angles=[radians(45),radians(-50),radians(-45)]

    motionProxy.setAngles(names, angles, fractionMaxSpeed)
    
    
    #time.sleep(3.0)
    #motionProxy.setStiffnesses("Head", 0.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="192.168.0.11",
                        help="Robot ip address")
    parser.add_argument("--port", type=int, default=9559,
                        help="Robot port number")

    args = parser.parse_args()

    main(args.ip, args.port)
    
