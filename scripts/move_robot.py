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
    postureProxy.goToPosture("StandInit", 0.5)

    # Initialize the move
    motionProxy.moveInit()

    # First call of move API
    # with post prefix to not be bloquing here.
    motionProxy.post.moveTo(-0.3, 0.0, 0)
    
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

    # Second call of move API
    motionProxy.post.moveTo(0.3, 0.0, 0)

    # get the second foot steps vector
    footSteps2 = []
    try:
        footSteps2 = motionProxy.getFootSteps()
    except Exception, errorMsg:
        print str(errorMsg)
        PLOT_ALLOW = False

    # end experiment, begin compute

    # here we wait until the move process is over
    motionProxy.waitUntilMoveIsFinished()
    # then we get the final robot position
    robotPositionFinal = almath.Pose2D(motionProxy.getRobotPosition(False))

    # compute robot Move with the second call of move API
    # so between nextRobotPosition and robotPositionFinal
    robotMove = almath.pose2DInverse(nextRobotPosition)*robotPositionFinal
    print "Robot Move:", robotMove

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

    # Second call of move API
    motionProxy.post.moveTo(-0.3, 0.0, 0)

    # get the second foot steps vector
    footSteps2 = []
    try:
        footSteps2 = motionProxy.getFootSteps()
    except Exception, errorMsg:
        print str(errorMsg)
        PLOT_ALLOW = False

    # end experiment, begin compute

    # here we wait until the move process is over
    motionProxy.waitUntilMoveIsFinished()
    # then we get the final robot position
    robotPositionFinal = almath.Pose2D(motionProxy.getRobotPosition(False))

    # compute robot Move with the second call of move API
    # so between nextRobotPosition and robotPositionFinal
    robotMove = almath.pose2DInverse(nextRobotPosition)*robotPositionFinal
    print "Robot Move:", robotMove


    # Go to rest position
    motionProxy.rest()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="192.168.0.11",
                        help="Robot ip address")
    parser.add_argument("--port", type=int, default=9559,
                        help="Robot port number")

    args = parser.parse_args()
    main(args.ip, args.port)
