from __future__ import print_function
from __future__ import division

from math import pi
from time import sleep

from .utils import read_config
from .imagereaders import NaoImageReader
from .finders import BallFinder, GoalFinder
from .movements import NaoMover


class Striker(object):

    def __init__(self, nao_ip, nao_port, res, red_hsv, white_hsv,
                 min_radius, run_after):
        self.mover = NaoMover(nao_ip=nao_ip, nao_port=nao_port)
        self.mover.stand_up()
        self.video_top = NaoImageReader(nao_ip, port=nao_port, res=res,
                                        fps=30, cam_id=0)
        self.video_bot = NaoImageReader(nao_ip, port=nao_port, res=res,
                                        fps=30, cam_id=1)
        self.ball_finder = BallFinder(red_hsv[0], red_hsv[1], min_radius, None)
        self.goal_finder = GoalFinder(white_hsv[0], white_hsv[1])
        self.lock_counter = 0
        self.loss_counter = 0
        self.run_after = run_after

    def ball_scan(self):
        yaw = self.mover.get_head_angles()[0]
        mag = abs(yaw)
        sign = 1 if yaw >= 0 else -1
        if mag > 2:
            self.mover.move_to(0, 0, sign * pi / 12)
        else:
            self.mover.change_head_angles(sign * pi / 4, 0, 0.5)

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

    def ball_tracking(self):
        cams = [self.video_top, self.video_bot]
        in_sight = False
        for cam in cams:
            ball_angles = self.get_ball_angles_from_camera(self, cam)
            if ball_angles is not None:
                x, y = ball_angles
                in_sight = True
                self.loss_counter = 0
                break

        if not in_sight:
            print('No ball in sight')
            self.loss_counter += 1
            if self.loss_counter > 5:
                self.ball_scan()
            return False

        if abs(x) > 0.05:
            self.turn_to_ball(x, y)
            return False
        else:
            return True

    def run_after(self):
        self.mover.move_to(0.3, 0, 0)

    def turn_to_ball(self, ball_x, ball_y):
        d_yaw, d_pitch = ball_x, 0
        print('ball yaw', d_yaw)

        if (abs(d_yaw) > 0.01):
            self.mover.change_head_angles(d_yaw, d_pitch,
                                          abs(d_yaw) / 2)
            sleep(1)
            self.mover.wait()

        yaw = self.mover.get_head_angles()[0]
        print('head yaw', yaw)
        if abs(yaw) > 0.05:
            print('Going to rotate')
            self.mover.set_head_angles(0, 0, 0.5)
            self.mover.move_to(0, 0, yaw)
            self.mover.wait()

    def align_to_goal(self):
        ball_angles = self.get_ball_angles_from_camera(self.video_bot)
        if ball_angles is None:
            raise ValueError('No ball')
        x, y = ball_angles

        print(x, y)
        if abs(x) > 0.05:
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

#        +----> Ball tracking until lock <--------------+
#        |       (search + rotation)                    |
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

if __name__ == '__main__':

    cfg = read_config()
    striker = Striker(
        nao_ip=cfg['ip'],
        nao_port=cfg['port'],
        res=cfg['res'],
        red_hsv=cfg['red'],
        white_hsv=cfg['white'],
        min_radius=cfg['min_radius'],
    )
    try:
        state = 'tracking'
        while True:
            if state == 'tracking':
                if striker.ball_tracking():
                    state = 'try_align'
            if state == 'try_align':
                if (striker.get_ball_angles_from_camera(striker.video_bot)
                    is not None):
                    state = 'align'
                else:
                    striker.run_after()
                    state = 'tracking'
            if state == 'align':
                try:
                    success = striker.align_to_goal()
                    if success:
                        state = 'kick'
                except ValueError:
                    state = 'tracking'
            if state == 'kick':
                print('YEEEEEEEE')
                break
    finally:
        striker.close()
