from __future__ import print_function
from __future__ import division

from math import pi
from time import sleep, time

from .utils import read_config
from .imagereaders import NaoImageReader
from .finders import BallFinder, GoalFinder
from .movements import NaoMover
import argparse
from naoqi import ALProxy
from threading import Thread


class Striker(object):

    def __init__(self, nao_ip, nao_port, res, ball_hsv, goal_hsv,
                 ball_min_radius, run_after):
        self.mover = NaoMover(nao_ip=nao_ip, nao_port=nao_port)
        self.mover.stand_up()
        self.upper_camera = NaoImageReader(nao_ip, port=nao_port, res=res,
                                           fps=30, cam_id=0)
        self.lower_camera = NaoImageReader(nao_ip, port=nao_port, res=res,
                                           fps=30, cam_id=1)
        self.ball_finder = BallFinder(tuple(ball_hsv[0]), tuple(ball_hsv[1]),
                                      ball_min_radius)
        self.goal_finder = GoalFinder(tuple(goal_hsv[0]), tuple(goal_hsv[1]))
        self.lock_counter = 0
        self.loss_counter = 0
        self.run_after = run_after
        self.in_move = False
        self.speaker = ALProxy("ALTextToSpeech",bytes(nao_ip),nao_port)
        self.speaker.setParameter("pitchShift",2)
        self.speaker.setParameter("speed",50)
        self.tts_thread = None
        self.last_speak = None

    def speak(self, text):
        if (self.tts_thread is None or not self.tts_thread.isAlive() ) and text!=self.last_speak:
            self.tts_thread = Thread(
                target=lambda text: self.speaker.say(str(text)),
                args=(text,)
            )
            self.tts_thread.start()
            self.last_speak=text
        
        
    
    def ball_scan(self):
        """Intelligently rotate the robot to search for stuff."""
        yaw = self.mover.get_head_angles()[0]
        mag = abs(yaw)

        # determine direction of head rotation
        sign = 1 if yaw >= 0 else -1

        # the robot starts to move arround his z-Axis in the direction where his
        # head is aligned when the head yaw angle has reached his maximum
        if mag > 2:
            self.mover.move_to(0, 0, sign * pi / 12)
            self.speak("Where is the ball? I am searching for it")
        # rotate head to the left, if head yaw angle is equally zero or larger
        # rotate head to the right, if head yaw angle is smaller than zero
        else:
            #self.speak("I have found the ball")
            self.mover.change_head_angles(sign * pi / 4, 0, 0.5)

    def get_ball_angles_from_camera(self, cam):
        """Detect the ball and return its angles in camera coordinates."""
        ball = self.ball_finder.find(cam.get_frame())
        if ball is None:
            return None

        (x, y), _ = ball
        x, y = cam.to_relative(x, y)
        x, y = cam.to_angles(x, y)
        return x, y

    def distance_to_ball(self):
        return 0.5

    def ball_tracking(self):
        """Track the ball using the feed from top and bottom camera.

        Returns
        -------
        bool
            True if robot is nicely aligned to ball; else False.

        """
        cams = [self.upper_camera, self.lower_camera]
        in_sight = False

        for cam in cams:
            ball_angles = self.get_ball_angles_from_camera(cam)
            if ball_angles is not None:
                x, y = ball_angles
                in_sight = True
                self.loss_counter = 0
                break

        if not in_sight:
            print('No ball in sight')
            self.loss_counter += 1

            # if ball is not in sight for more than five consecutive frames,
            # start a ball scan
            if self.loss_counter > 5:
                self.ball_scan()
            return False

        # turn to ball, if the angle between the ball and the robot is too big
        if abs(x) > 0.15:
            #self.speak('Align to the ball')
            self.mover.stop_moving()
            self.turn_to_ball(x, y)
            return False
        else:
            return True

    def run_to_ball(self):
        self.mover.move_to(1, 0, 0)

    def turn_to_ball(self, ball_x, ball_y):
        """Align robot to the ball.

        If head is not centered at the ball (within tolerance), then
        turn head to ball. If after that the angle of head to body
        becomes too big, rotate the body by the head angle and
        simultaneously rotate head into 0 position to achieve alignment.
        """

        # only the x ball angle is relevant for alignment
        d_yaw, d_pitch = ball_x, 0
        print('ball yaw:', d_yaw)

        # center head at the ball
        if (abs(d_yaw) > 0.01):
            self.mover.change_head_angles(d_yaw, d_pitch,
                                          abs(d_yaw) / 2)
            sleep(1)
            self.mover.wait()

        yaw = self.mover.get_head_angles()[0]
        print('head yaw', yaw)

        # align body with the head
        if abs(yaw) > 0.05:
            print('Going to rotate')
            self.speak("Going to rotate")
            self.mover.set_head_angles(0, 0, 0.5)
            self.mover.move_to(0, 0, yaw)
            self.mover.wait()


    def align_to_ball(self):
        ball_angles = self.get_ball_angles_from_camera(self.lower_camera)
        if ball_angles is None:
            raise ValueError('No ball')
        x, y = ball_angles
        goal_x, goal_y = 0.115, 0.32
        dx, dy = goal_x - x, goal_y - y
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            print(x, y)
            return True
        if abs(dy) > 0.05:
            self.mover.move_to(dy * 0.5, 0, 0)
            self.mover.wait()
        if abs(dx) > 0.05:
            self.mover.move_to(0, -dx * 0.5, 0)
            self.mover.wait()
        return False

    def align_to_goal(self):
        ball_angles = self.get_ball_angles_from_camera(self.lower_camera)
        if ball_angles is None:
            raise ValueError('No ball')
        x, y = ball_angles

        print(x, y)
        if abs(x) > 0.1:
            self.turn_to_ball(x, y)
            return False

        if y > 0.35:
            self.mover.move_to(-0.05, 0, 0)
            self.mover.wait()
            return False
        elif y < 0.25:
            self.mover.move_to(0.05, 0, 0)
            self.mover.wait()
            return False

        goal_contour = self.goal_finder.find(self.upper_camera.get_frame())
        if goal_contour is not None:
            goal_center_x = self.goal_finder.goal_center(goal_contour)
            gcx_rel, _ = self.upper_camera.to_relative(goal_center_x, 0)
            if abs(gcx_rel - 0.5) > 0.1:
                increment = 0.1 if gcx_rel > 0.5 else -0.1
            else:
                print('Alignment achieved')
                return True
        else:
            increment = 0.1
            print('No goal found, doing random stuff')

        self.mover.move_to(0, increment, 0)
        self.mover.wait()
        return False

    def close(self):
        self.mover.rest()
        self.upper_camera.close()
        self.lower_camera.close()

# ____________________ STRIKER __________________________
#
#        +----> Ball tracking (see below) <-------------+
#        |                                              |
#        |               |                              |
#        |               |                              |
#        |               v                              |
#        |          Try goal align                      |
#        |              /  \                            |
#   lost |      can do /    \ cannot do                 |
#   ball |            v      v                          |
#        +-- Align until   Ball is only in top camera --+
#             success.          Move closer.
#                |
#     successful |
#                v
#             Kick it!
#
# _______________________________________________________

# ____________________ TRACKING _________________________
#
#                        yes
# check if ball visible ---> rotate head to the ball
#     ^            |                    |
#     |            | no                 |
#     |            v                    |
#     +--- ball scan rotation           |
#     |                                 |
#     |                  no             V
#     |               +---------- already rotating body?
#     |               |                 |
#     |               v                 | yes
#     |       head angle too big?       v
#     |             /  \            head angle
#     |        yes /    \ no     is below threshold?
#     |           v      v              |         |
#     |        stop    successful       | no      | yes
#     |       moving      exit          |         v
#     +----- and start                  |    stop rotating body
#     |    rotating body                |         |
#     |                                 |         |
#     +---------------------------------+---------+
#
# _______________________________________________________


if __name__ == '__main__':

    cfg = read_config()
    striker = Striker(
        nao_ip=cfg['ip'],
        nao_port=cfg['port'],
        res=cfg['res'],
        ball_hsv=cfg['ball'],
        goal_hsv=cfg['goal'],
        ball_min_radius=cfg['ball_min_radius'],
        run_after=False
    )

    # allow additional arguments when running the function like
    # stand
    # rest
    # kick
    # if no argument is given the state machine is run

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--stand", action="store_true",
                        help="let the robot stand up")
    parser.add_argument("-k", "--kick", action="store_true",
                        help="let the robot do a fancy kick")
    parser.add_argument("-r", "--rest", action="store_true",
                        help="let the robot rest")

    args = parser.parse_args()

    if args.stand:
        striker.mover.stand_up()

    elif args.rest:
        striker.mover.rest()

    # perform a fancy kick
    elif args.kick:
        striker.mover.stand_up()
        striker.mover.kick()
        striker.mover.rest()


    # perform normal state-machine if no input argument is given
    # (see diagram above)
    else:
        try:  # Hit Ctrl-C to stop, cleanup and exit
            state = 'tracking'
            #t = None
            while True:
                # meassure time for debbuging
                loop_start = time()
                print('State:', state)
                #striker.speak(str(state))
                
                if state == 'tracking':
                    # start ball approach when ball is visible
                    if striker.ball_tracking():
                        striker.speak("ball_approach")
                        state = 'ball_approach'

                elif state == 'ball_approach':
                    ball_in_lower = striker.get_ball_angles_from_camera(
                        striker.lower_camera
                    )
                    print(ball_in_lower)
                    if (ball_in_lower is not None and ball_in_lower[1] > 0.28):
                        
                        #t = Thread(target=striker.speak, args=["Ball is close enough, stop approach"])
                        #t.start()
                        print('Ball is close enough, stop approach')
                        #striker.speak("Ball is close enough stop approach")
                        #striker.mover.stop_moving()
                        #state = 'align'
                        state='simple_kick'
                    else:
                        print('Continue running')
                        ##striker.speak("Continue running")
                        striker.run_to_ball()
                        state = 'tracking'

                elif state == 'simple_kick':
                    #striker.mover.set_head_angles(0,0.25,0.3)
                    print('Doing the simple kick')

                    # just walk a short distance forward, ball should be near
                    # and it will probably be kicked in the right direction
                    striker.speak("Simple Kick")
                    striker.mover.move_to(0.3,0,0)
                    striker.mover.wait()
                    state = 'tracking'

                elif state == 'align':
                    striker.mover.set_head_angles(0, 0.25, 0.3)
                    sleep(0.5)
                    try:
                        success = striker.align_to_ball()
                        sleep(0.3)
                        if success:
                            state = 'kick'
                    except ValueError:
                        striker.mover.set_head_angles(0, 0, 0.3)
                        state = 'tracking'

                elif state == 'kick':
                    print('KICK!')
                    striker.mover.kick()
                    break

                loop_end = time()
                print('Loop time:', loop_end - loop_start)
        finally:
            striker.close()
