# -*- encoding: UTF-8 -*-

''' PoseInit: Small example to make Nao go to an initial position. '''
# syntax: python motion_setter.py 0 		-> Robot stands up
#         python motion_setter.py 1		-> Robot goes back to rest position

import argparse
from naoqi import ALProxy
import sys

def main(robotIP, PORT,rest):
#def main(reset):
  
    motionProxy  = ALProxy("ALMotion", robotIP, PORT)
    postureProxy = ALProxy("ALRobotPosture", robotIP, PORT)
    AutonomousLifeProxy = ALProxy("ALAutonomousLife", robotIP,PORT)

    # Disable autonomous life
    AutonomousLifeProxy.setState("disabled")

    # Wake up robot
    motionProxy.wakeUp()

    # set the stiffnes
    motionProxy.setStiffnesses("Head", 1.0)
    motionProxy.setStiffnesses("RHand", 1.0)	
    motionProxy.setStiffnesses("LHand", 1.0)
    motionProxy.setStiffnesses("LShoulderPitch", 1.0)
    motionProxy.setStiffnesses("LShoulderRoll", 1.0)
    motionProxy.setStiffnesses("LElbowRoll", 1.0)
    motionProxy.setStiffnesses("LWristYaw", 1.0)
    motionProxy.setStiffnesses("LElbowYaw", 1.0)
    motionProxy.setStiffnesses("LHipYawPitch", 1.0)
    motionProxy.setStiffnesses("LHipPitch", 1.0)
    motionProxy.setStiffnesses("LKneePitch", 1.0)
    motionProxy.setStiffnesses("LAnklePitch", 1.0)
    motionProxy.setStiffnesses("LHipRoll", 1.0)
    motionProxy.setStiffnesses("LAnkleRoll", 1.0)
    
    motionProxy.setStiffnesses("RShoulderPitch", 1.0)
    motionProxy.setStiffnesses("RShoulderRoll", 1.0)
    motionProxy.setStiffnesses("RElbowRoll", 1.0)
    motionProxy.setStiffnesses("RWristYaw", 1.0)
    motionProxy.setStiffnesses("RElbowYaw", 1.0)
    motionProxy.setStiffnesses("RHipYawPitch", 1.0)
    motionProxy.setStiffnesses("RHipPitch", 1.0)
    motionProxy.setStiffnesses("RKneePitch", 1.0)
    motionProxy.setStiffnesses("RAnklePitch", 1.0)
    motionProxy.setStiffnesses("RHipRoll", 1.0)
    motionProxy.setStiffnesses("RAnkleRoll", 1.0)

    # Send robot to Stand Init
    #postureProxy.goToPosture("StandInit", 0.5)

    # Go to rest position
    #print("")
    #if reset==1:
    #	    motionProxy.rest()
    rest=int(rest)
    if rest==1:
        motionProxy.rest()
    else:
        postureProxy.goToPosture("StandInit", 0.5)

    
	    

if __name__ == "__main__":
    #parser = argparse.ArgumentParser()
    #parser.add_argument("--ip", type=str, default="192.168.0.11",
    #                    help="Robot ip address")
    #parser.add_argument("--port", type=int, default=9559,
    #                    help="Robot port number")

    print(sys.argv[1])
    rest=sys.argv[1]
    #args = parser.parse_args()
#    main(args.ip, args.port,reset)
    
    main("192.168.0.11",9559,rest)
