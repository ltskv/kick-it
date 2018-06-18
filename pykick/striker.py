from __future__ import print_function
from __future__ import division

from math import pi
from time import sleep, time

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
        self.ball_finder = BallFinder(tuple(red_hsv[0]), tuple(red_hsv[1]),
                                      min_radius)
        self.goal_finder = GoalFinder(white_hsv[0], white_hsv[1])
        self.lock_counter = 0
        self.loss_counter = 0
        self.run_after = run_after
        self.in_move = False

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
            ball_angles = self.get_ball_angles_from_camera(cam)
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

        if abs(x) > 0.15:
            self.mover.stop_moving()
            self.turn_to_ball(x, y)
            return False
        else:
            return True

    def run_to_ball(self):
        self.mover.move_to(1, 0, 0)

    def turn_to_ball(self, ball_x, ball_y):
        d_yaw, d_pitch = ball_x, 0
        print('ball yaw:', d_yaw)

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
        run_after=False
    )
    try:
        state = 'tracking'
        while True:
            loop_start = time()
            print('State:', state)
            if state == 'tracking':
                if striker.ball_tracking():
                    state = 'ball_approach'

            elif state == 'ball_approach':
                ball_in_lower = striker.get_ball_angles_from_camera(
                    striker.video_bot
                )

                print(ball_in_lower)
                if (ball_in_lower is not None
                    and ball_in_lower[1] > 0.28):

                    print('Ball is in lower camera, go to align')
                    striker.mover.stop_moving()
                    state = 'align'
                else:
                    print('Continue running')
                    striker.run_to_ball()
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
