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
        self.finder = BallFinder(red_hsv[0], red_hsv[1], min_radius, None)
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
        try:
            (x, y), _ = self.finder.find_colored_ball(
                cam.get_frame()
            )
            self.loss_counter = 0
            x, y = cam.to_relative(x, y)
            x, y = cam.to_angles(x, y)
            return x, y
        except TypeError:
            raise ValueError('Ball not found')


    def ball_tracking(self):
        cams = [self.video_top, self.video_bot]
        in_sight = False
        for cam in cams:
            try:
                x, y = self.get_ball_angles_from_camera(self, cam)
                in_sight = True
                break
            except ValueError:
                pass

        if not in_sight:
            print('No ball in sight')
            self.loss_counter += 1
            if self.loss_counter > 5:
                self.ball_scan()
            return

        self.turn_to_ball(x, y)

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
        try:
            x, y = self.get_ball_angles_from_camera(self.video_bot)
            print(x, y)
            if abs(x) > 0.05:
                self.turn_to_ball(x, y)
                return
        except Exception as e:
            print(e)
            print('No ball')
            sleep(0.1)
            return

        print('moving')
        increment = 0.1
        if y > 0.35:
            self.mover.move_to(-0.05, 0, 0)
        elif y < 0.25:
            self.mover.move_to(0.05, 0, 0)
        self.mover.wait()
        self.mover.move_to(0, increment, 0)
        self.mover.wait()


    def close(self):
        self.mover.rest()
        self.video_top.close()
        self.video_bot.close()


if __name__ == '__main__':

    cfg = read_config()
    follower = Striker(
        nao_ip=cfg['ip'],
        nao_port=cfg['port'],
        res=cfg['res'],
        red_hsv=cfg['red'],
        white_hsv=cfg['white'],
        min_radius=cfg['min_radius'],
        run_after=False
    )
    try:
        while True:
            try:
                print(follower.get_ball_angles_from_camera(
                    follower.video_bot)[1])
            except Exception as e:
                print(e)

    finally:
        follower.close()
