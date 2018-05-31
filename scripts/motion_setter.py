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
    # motionProxy.wakeUp()

    # stiffnessses
    # hand and wrist
    handStiffness = 0.0;
    # shoulder and elbow
    armStiffness = 0.0;
    # head
    headStiffness = 0.9;
    # hip
    hipStiffness = 0.9;
    # knee
    kneeStiffness = 0.9;
    # ankle
    ankleStiffness = 0.9;


    # set the stiffnes
    motionProxy.setStiffnesses("Head", headStiffness)
    motionProxy.setStiffnesses("RHand", handStiffness)	
    motionProxy.setStiffnesses("LHand", handStiffness)
    motionProxy.setStiffnesses("LShoulderPitch", armStiffness)
    motionProxy.setStiffnesses("LShoulderRoll", armStiffness)
    motionProxy.setStiffnesses("LElbowRoll", armStiffness)
    motionProxy.setStiffnesses("LWristYaw", handStiffness)
    motionProxy.setStiffnesses("LElbowYaw", armStiffness)
    motionProxy.setStiffnesses("LHipYawPitch", hipStiffness)
    motionProxy.setStiffnesses("LHipPitch", hipStiffness)
    motionProxy.setStiffnesses("LKneePitch", kneeStiffness)
    motionProxy.setStiffnesses("LAnklePitch", ankleStiffness)
    motionProxy.setStiffnesses("LHipRoll", hipStiffness)
    motionProxy.setStiffnesses("LAnkleRoll", ankleStiffness)
    
    motionProxy.setStiffnesses("RShoulderPitch", armStiffness)
    motionProxy.setStiffnesses("RShoulderRoll", armStiffness)
    motionProxy.setStiffnesses("RElbowRoll", armStiffness)
    motionProxy.setStiffnesses("RWristYaw", handStiffness)
    motionProxy.setStiffnesses("RElbowYaw", armStiffness)
    motionProxy.setStiffnesses("RHipYawPitch", hipStiffness)
    motionProxy.setStiffnesses("RHipPitch", hipStiffness)
    motionProxy.setStiffnesses("RKneePitch", kneeStiffness)
    motionProxy.setStiffnesses("RAnklePitch", ankleStiffness)
    motionProxy.setStiffnesses("RHipRoll", hipStiffness)
    motionProxy.setStiffnesses("RAnkleRoll", ankleStiffness)

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
