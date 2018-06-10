from naoqi import ALProxy
from naoqi import ALBroker
from naoqi import ALModule
import time

NAO_IP = "192.168.0.11"

# Global variable to store the BallSearcher module instance
BallSearcher = None
memory = None
ball_proxy = None
ball_found = False


class BallSearcherModule(ALModule):
    """ A simple module able to react to facedetection events"""

    def __init__(self, name):
        ALModule.__init__(self, name)
        # No need for IP and port here because
        # we have our Python broker connected to NAOqi broker

        # Create a proxy to ALTextToSpeech for later use
        self.tts = ALProxy("ALTextToSpeech")
        self.tts.setParameter('speed', 100)
        self.mp = ALProxy('ALMotion')
        self.mp.setStiffnesses("Head", 1.0)

        # Subscribe to the BallDetected event:
        global memory
        global ball_proxy
        global ball_found
        ball_proxy = ALProxy('ALRedBallDetection')
        ball_proxy.subscribe('detector')
        memory = ALProxy("ALMemory")
        memory.subscribeToEvent("redBallDetected",
            "BallSearcher",
            "onBallDetected")

    def searchForBall(self):
        names = ["HeadYaw", "HeadPitch"]
        sleep_period = 0.8
        fractionMaxSpeed = 0.5
        i=0
        while i<2:
            time.sleep(sleep_period)
            if ball_found:
                return
            print i
            angles = [i,0]
            self.mp.setAngles(names, angles, fractionMaxSpeed)
            i=float(i)+3.14/4

        # go back to middle position
        time.sleep(sleep_period)
        if ball_found:
            return
        print 'go back'
        angles = [0,0]
        self.mp.setAngles(names, angles, fractionMaxSpeed)

        # go into the right direction
        i=0
        while i > -2:
            time.sleep(sleep_period)
            if ball_found:
                return
            print i
            angles = [i,0]
            self.mp.setAngles(names, angles, fractionMaxSpeed)
            i=i-3.14/4

        # go back to middle position
        time.sleep(sleep_period)
        if ball_found:
            return
        print "get back"
        angles = [0,0]
        self.mp.setAngles(names, angles, fractionMaxSpeed)

    def onBallDetected(self, *_args):
        """ This will be called each time a ball is detected."""

        # Unsubscribe to the event when talking, to avoid repetitions
        memory.unsubscribeToEvent("redBallDetected", "BallSearcher")
        # time.sleep(0.1)
        global ball_found
        ball_found = True
        print 'gotcha'
        self.tts.say("Hello, ball")

        # Subscribe again to the event
        # memory.subscribeToEvent("redBallDetected",
            # "BallSearcher",
            # "onBallDetected")


def main():
    """ Main entry point."""

    # We need this broker to be able to construct
    # NAOqi modules and subscribe to other modules
    # The broker must stay alive until the program exists
    myBroker = ALBroker(
        "myBroker",
        "0.0.0.0",
        0,
        '192.168.0.11',
        9559
    )


    # Warning: BallSearcher must be a global variable
    # The name given to the constructor must be the name of the
    # variable
    global BallSearcher
    BallSearcher = BallSearcherModule("BallSearcher")
    BallSearcher.searchForBall()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print "Interrupted by user, shutting down"
        myBroker.shutdown()


if __name__ == "__main__":
    main()
