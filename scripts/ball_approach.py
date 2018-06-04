from __future__ import print_function
from __future__ import division

from utils import read_config

from imagereaders import NaoImageReader
from finders import BallFinder
from movements import NaoMover


class BallFollower(object):

    def __init__(self, nao_ip, nao_port, res, hsv_lower, hsv_upper,
                 min_radius):
        self.mover = NaoMover(nao_ip=nao_ip, nao_port=nao_port)
        self.mover.stand_up()
        self.video_top = NaoImageReader(nao_ip, port=nao_port, res=res,
                                        fps=30, cam_id=0)
        self.video_bot = NaoImageReader(nao_ip, port=nao_port, res=res,
                                        fps=30, cam_id=0)
        self.finder = BallFinder(hsv_lower, hsv_upper, min_radius, None)
        self.counter = 0

    def update(self):
        print('in update loop')
        try:
            (x, y), radius = self.finder.find_colored_ball(
                self.video_top.get_frame()
            )
            x, y = self.video_top.to_relative(x, y)
            print('Top camera')
        except TypeError:
            try:
                (x, y), radius = self.finder.find_colored_ball(
                    self.video_bot.get_frame()
                )
                x, y = self.video_bot.to_relative(x, y)
                print('Low camera')
            except TypeError:
                return
        print(x, y)
        self.process_coordinates(x, y)

    def process_coordinates(self, x, y):
        x_diff = x - 0.5
        y_diff = y - 0.5
        print("x_diff: " + str(x_diff))
        print("y_diff: " + str(y_diff))

        d_yaw, d_pitch = -x_diff / 2, 0

        if abs(x_diff) > 0.1:
            self.mover.change_head_angles(d_yaw, d_pitch, 0.3)
            self.counter = 0
        else:
            self.counter += 1
            print(self.counter)
        if self.counter == 4:
            self.counter = 0
            print('Going to rotate')
            head_angle = self.mover.get_head_angles()
            if abs(head_angle[0]) > 0.1:
                self.mover.set_head_angles(0, 0, 0.05)
                self.mover.move_to(0, 0, head_angle[0])
                self.mover.wait()
            self.mover.move_to(0.3, 0, 0)

    def close(self):
        self.video_top.close()
        self.video_bot.close()


if __name__ == '__main__':

    cfg = read_config()
    follower = BallFollower(
        nao_ip=cfg['ip'],
        nao_port=cfg['port'],
        res=cfg['res'],
        hsv_lower=tuple(map(cfg.get, ('low_h', 'low_s', 'low_v'))),
        hsv_upper=tuple(map(cfg.get, ('high_h', 'high_s', 'high_v'))),
        min_radius=cfg['min_radius']
    )
    try:
        while True:
            follower.update()
    finally:
        follower.close()
