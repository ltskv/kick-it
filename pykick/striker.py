from __future__ import print_function
from __future__ import division

from math import pi
from time import sleep, time

from .utils import read_config
from .imagereaders import NaoImageReader
from .finders import BallFinder, GoalFinder
from .movements import NaoMover
import sys

class Striker(object):

    def __init__(self, nao_ip, nao_port, res, ball_hsv, goal_hsv,
                 ball_min_radius, run_after):
        self.mover = NaoMover(nao_ip=nao_ip, nao_port=nao_port)
        self.mover.stand_up()
        self.video_top = NaoImageReader(nao_ip, port=nao_port, res=res,
                                        fps=30, cam_id=0)
        self.video_bot = NaoImageReader(nao_ip, port=nao_port, res=res,
                                        fps=30, cam_id=1)
        self.ball_finder = BallFinder(tuple(ball_hsv[0]), tuple(ball_hsv[1]),
                                      ball_min_radius)
        self.goal_finder = GoalFinder(tuple(goal_hsv[0]), tuple(goal_hsv[1]))
        self.lock_counter = 0
        self.loss_counter = 0
        self.run_after = run_after
        self.in_move = False

    # this function will scan for the ball, if it is not in sight
    def ball_scan(self):

        # determine current head angle
        yaw = self.mover.get_head_angles()[0]
        mag = abs(yaw)

        # determine direction of head rotation
        sign = 1 if yaw >= 0 else -1

        # the robot starts to move arround his z-Axis in the direction where his head is aligned
        # when the head yaw angle has reached his maximum
        if mag > 2:
            self.mover.move_to(0, 0, sign * pi / 12)

        # rotate head to the left, if head yaw angle is equally zero or larger
        # rotate head to the right, if head yaw angle is smaller than zero
        else:
            self.mover.change_head_angles(sign * pi / 4, 0, 0.5)

    # this function detects the ball in the view of a given camera view
    # and returns the angles of the ball to the camera
    def get_ball_angles_from_camera(self, cam):
        ball = self.ball_finder.find_colored_ball(
            cam.get_frame()
        )
        if ball is None:
            return None

        (x, y), _ = ball
        x, y = cam.to_relative(x, y)
        x, y = cam.to_angles(x, y)
        return x, y

    def distance_to_ball(self):
        return 0.5

    # this function tracks the ball in the camera views
    def ball_tracking(self):

        # get video streams from both cameras
        cams = [self.video_top, self.video_bot]
        in_sight = False

        # try to determine the angle of the ball to the cameras in both streams
        for cam in cams:
            ball_angles = self.get_ball_angles_from_camera(cam)

            # check if the ball angles could be determined                        
            if ball_angles is not None:

                # safe ball angles in x,y
                x, y = ball_angles

                # ball is in view -> set in_sight variable to true
                in_sight = True

                # reset ball loss counter
                self.loss_counter = 0
                break

        # actions, if the ball is not in sight
        if not in_sight:
            print('No ball in sight')

            # increase ball loss counter
            self.loss_counter += 1

            # if ball is not in view for more than five times,
            # start a ball scan
            if self.loss_counter > 5:
                self.ball_scan()
            return False

        # check if the x angle between the robot and the ball is above a specific threshold
        if abs(x) > 0.15:

            # stop the robot, if the angle is to large
            self.mover.stop_moving()
            
            # align the robot to the ball
            self.turn_to_ball(x, y)
            return False
        else:
            return True

    def run_to_ball(self):
        self.mover.move_to(1, 0, 0)

    # this function aligns the robot to the ball
    def turn_to_ball(self, ball_x, ball_y):

        # only the x ball angle is relevant for the rotation
        d_yaw, d_pitch = ball_x, 0
        print('ball yaw:', d_yaw)

        # check if the angle between the robot and the ball is above a specific threshold
        if (abs(d_yaw) > 0.01):
            
            # try to align camera with the ball
            self.mover.change_head_angles(d_yaw, d_pitch,
                                          abs(d_yaw) / 2)
            sleep(1)
            self.mover.wait()

        # determine current head angle to estimate
        # how far the robot has to rotate arround the z-Axis
        yaw = self.mover.get_head_angles()[0]
        print('head yaw', yaw)

        # determine if the angle of the head to the body is above a specific threshold
        if abs(yaw) > 0.05:       
            print('Going to rotate')

            # change the head angles to 0 0
            self.mover.set_head_angles(0, 0, 0.5)

            # rotate robot arround the z-Axis for the estimated angle
            self.mover.move_to(0, 0, yaw)
            self.mover.wait()

    
    def align_to_ball(self):
        ball_angles = self.get_ball_angles_from_camera(self.video_bot)
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
        ball_angles = self.get_ball_angles_from_camera(self.video_bot)
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

        goal_contour = self.goal_finder.find_goal_contour(
            self.video_top.get_frame()
        )
        if goal_contour is not None:
            goal_center_x = self.goal_finder.goal_center(goal_contour)
            gcx_rel, _ = self.video_top.to_relative(goal_center_x, 0)
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
        self.video_top.close()
        self.video_bot.close()

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

    # try to readout arguments
    try:
        args=sys.argv[1]   
    except NameError:
        args=''

    # check input argument
    if args:

        # bring robot in stand_up position
        if args == 'stand': 
            striker.mover.stand_up()

        # bring robot in rest postion
        elif args == 'rest':
            striker.mover.rest()

        # perform a fancy kick
        elif args == 'kick':
            striker.mover.stand_up()
            striker.mover.kick()
            striker.mover.rest()
    
    # perform normal state-machine if no input argument is given
    else:
    
	    try:
		# start with ball tracking first        
		state = 'tracking'
		
		# state machine of the striker
		while True:

		    # start time meassure for debbuging
		    loop_start = time()

		    # print the current state of the state machine
		    print('State:', state)

		    # actions in the tracking state
		    if state == 'tracking':

		        # start ball approach when ball is visible
		        if striker.ball_tracking():
		            state = 'ball_approach'

		    # actions in the ball_approach state
		    elif state == 'ball_approach':

		        # get the angle of the ball in the picture of the lower camera
		        ball_in_lower = striker.get_ball_angles_from_camera(
		            striker.video_bot
		        )

		        # print the angle of the ball in the lower camera
		        print(ball_in_lower)

		        # check if the ball is in the lower camera
		        # and the angle is above a specific threshold (ball is close enough)
		        if (ball_in_lower is not None
		            and ball_in_lower[1] > 0.28):

		            print('Ball is in lower camera, go to align')
		            #striker.mover.stop_moving()
		            #state = 'align'

		            # perform a simple kick
		            state='simple_kick'

		        # continue moving, if the ball is not close enough
		        # or not in the view of the lower camera
		        else:
		            print('Continue running')
		            striker.run_to_ball()

		            # go back to the tracking state
		            state = 'tracking'

		    # actions in the simple_kick state
		    elif state == 'simple_kick':
		        #striker.mover.set_head_angles(0,0.25,0.3)
		        print('Doing the simple kick')

		        # just walk a short distance straight forward,
		        # as the ball should be straight ahead in a small distance
		        striker.mover.move_to(0.3,0,0)
		        striker.mover.wait()

		        # go back to the tracking state after the simple_kick
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

		    # stop time meassuring for debbuging and print the time of the loop
		    loop_end = time()
		    print('Loop time:', loop_end - loop_start)
	    finally:
		striker.close()
