from __future__ import print_function
from __future__ import division

from math import tan, pi

from .utils import read_config
from .imagereaders import NaoImageReader
from .finders import BallFinder
from .movements import NaoMover


class BallFollower(object):

    def __init__(self, nao_ip, nao_port, res, hsv_lower, hsv_upper,
                 min_radius, run_after):
        self.mover = NaoMover(nao_ip=nao_ip, nao_port=nao_port)
        self.mover.stand_up()
        self.video_top = NaoImageReader(nao_ip, port=nao_port, res=res,
                                        fps=30, cam_id=0)
        self.video_bot = NaoImageReader(nao_ip, port=nao_port, res=res,
                                        fps=30, cam_id=0)
        self.finder = BallFinder(hsv_lower, hsv_upper, min_radius, None)
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

    def update(self):
        #print('in update loop')
        try:
            (x, y), radius = self.finder.find_colored_ball(
                self.video_top.get_frame()
            )
            self.loss_counter = 0
            x, y = self.video_top.to_relative(x, y)
            x, y = self.video_top.to_angles(x,y)
            # print("y (in radians) angle is:"+str(angles[1]))
            # y_angle=angles[1]
            # y_angle=pi/2-y_angle-15*pi/180
            # distance = 0.5 * tan(y_angle)
            # print("Distance="+str(distance))
            # print('Top camera\n')
        except TypeError:
            try:
                (x, y), radius = self.finder.find_colored_ball(
                    self.video_bot.get_frame()
                )
                x, y = self.video_bot.to_relative(x, y)
                self.loss_counter = 0
                #print('Low camera')
            except TypeError:
                print('No ball in sight')
                self.loss_counter += 1
                if self.loss_counter > 5:
                    self.ball_scan()
                return
        #print(x, y)
        self.process_coordinates(x, y)

    def process_coordinates(self, x, y):
        # x_diff = x - 0.5
        # y_diff = y - 0.5
        # print("x_diff: " + str(x_diff))
        # print("y_diff: " + str(y_diff))

        d_yaw, d_pitch = x, 0
        print(d_yaw)
	
	# dont move the head, when the angle is below a threshold
	# otherwise function would raise an error and stop
	if (abs(d_yaw)>=0.00001):
		self.mover.change_head_angles(d_yaw * 0.7, d_pitch,
                                      abs(d_yaw) / 2)
	
        # self.counter = 0
        yaw = self.mover.get_head_angles()[0]
        if abs(yaw) > 0.4:
            # self.counter = 0
            print('Going to rotate')
            self.mover.set_head_angles(0, 0, 0.5)
            self.mover.move_to(0, 0, yaw)
            self.mover.wait()
        if self.run_after:
            self.mover.move_to(0.3, 0, 0)

    def close(self):
        self.mover.rest()
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
        min_radius=cfg['min_radius'],
        run_after=False
    )
    try:
        while True:
            follower.update()
    finally:
        follower.close()
