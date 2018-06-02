# -*- encoding: UTF-8 -*-

''' PoseInit: Small example to make Nao go to an initial position. '''

import argparse
from naoqi import ALProxy
import time
import math
import almath
#include <alproxies/alnavigationproxy.h>


def main(robotIP, PORT=9559):

    motionProxy  = ALProxy("ALMotion", robotIP, PORT)
    postureProxy = ALProxy("ALRobotPosture", robotIP, PORT)

    # Wake up robot
    motionProxy.wakeUp()
    
    handStiffness=0.0;
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
    postureProxy.goToPosture("StandInit", 0.5)

    # Initialize the move
    motionProxy.moveInit()

    # First call of move API
    # with post prefix to not be bloquing here.
    motionProxy.post.moveTo(0, 0.0, 0)
    
    # wait that the move process start running
    time.sleep(0.1)

    # get robotPosition and nextRobotPosition
    useSensors = False
    robotPosition     = almath.Pose2D(motionProxy.getRobotPosition(useSensors))
    nextRobotPosition = almath.Pose2D(motionProxy.getNextRobotPosition())

    # get the first foot steps vector
    # (footPosition, unChangeable and changeable steps)

    footSteps1 = []
    try:
        footSteps1 = motionProxy.getFootSteps()
    except Exception, errorMsg:
        print str(errorMsg)
        PLOT_ALLOW = False

    while True:
        cmd = int(raw_input(">"))

    # Second call of move API
        motionProxy.post.moveTo(3, 0, 0)

    # here we wait until the move process is over
        motionProxy.waitUntilMoveIsFinished()
   
    ''' 
     # Second call of move API
    motionProxy.post.moveTo(1.5, 0, 0)

     # here we wait until the move process is over
    motionProxy.waitUntilMoveIsFinished()

   
     # Second call of move API
    motionProxy.post.moveTo(0, -1.5, 0)
   
     # here we wait until the move process is over
    motionProxy.waitUntilMoveIsFinished()

      # Second call of move API
    motionProxy.post.moveTo(-1.5, 0, 0)

     # here we wait until the move process is over
    motionProxy.waitUntilMoveIsFinished()
    '''

      # Second call of move API
#    motionProxy.post.moveTo(0, 3, 0)

     # here we wait until the move process is over
 #   motionProxy.waitUntilMoveIsFinished()




    # Go to rest position
    #motionProxy.rest()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="192.168.0.11",
                        help="Robot ip address")
    parser.add_argument("--port", type=int, default=9559,
                        help="Robot port number")

    args = parser.parse_args()
    main(args.ip, args.port)
