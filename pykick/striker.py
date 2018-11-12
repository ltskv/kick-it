from __future__ import print_function
from __future__ import division

from threading import Thread
from math import pi, tan, asin, atan, radians
from time import sleep, time, strftime
from collections import deque

from .imagereaders import NaoImageReader
from .finders import BallFinder, GoalFinder, FieldFinder
from .movements import NaoMover
from naoqi import ALProxy


class Striker(object):

    def __init__(self, nao_ip, nao_port, res, ball_hsv, goal_hsv, field_hsv,
                 ball_min_radius, do_capture=False):

        # Maintenance
        self.run_id = strftime('%Y%m%d%H%M%S')
        self.is_over = False
        self.last_goal = 'right'
        self.doing_caputre = do_capture

        # Motion
        self.mover = NaoMover(nao_ip=nao_ip, nao_port=nao_port)

        # Sight
        self.upper_camera = NaoImageReader(
            nao_ip, port=nao_port, res=res, fps=10, cam_id=0,
        )
        self.lower_camera = NaoImageReader(
            nao_ip, port=nao_port, res=1, fps=10, cam_id=1,
        )

        # POV
        if do_capture:
            self.upper_pov = NaoImageReader(
                nao_ip, port=nao_port, res=1, fps=10, cam_id=0,
                video_file='./cam0_' + self.run_id + '.avi'
            )

            self.lower_pov = NaoImageReader(
                nao_ip, port=nao_port, res=1, fps=10, cam_id=1,
                video_file='./cam1_' + self.run_id + '.avi'
            )
            self.pov_thread = Thread(target=self._pov)
            self.pov_thread.start()

        # Recognition
        self.ball_finder = BallFinder(tuple(ball_hsv[0]), tuple(ball_hsv[1]),
                                      ball_min_radius)
        self.field_finder = FieldFinder(tuple(field_hsv[0]),
                                        tuple(field_hsv[1]))
        self.goal_finder = GoalFinder(tuple(goal_hsv[0]), tuple(goal_hsv[1]))

        # Talking
        self.player = ALProxy('ALAudioPlayer', bytes(nao_ip), nao_port)
        self.tts = ALProxy('ALTextToSpeech', bytes(nao_ip), nao_port)
        self.speach_queue = deque(maxlen=4)
        self.speach_history = []
        self.tts_thread = Thread(target=self._speaker)
        self.tts_thread.start()

        # Debugging
        self._timer_start = 0
        self._timer_stop = 0

    def close(self):
        self.is_over = True

        if self.tts_thread.isAlive():
            self.tts_thread.join()
        if self.doing_caputre and self.pov_thread.isAlive():
            self.pov_thread.join()
            self.upper_pov.close()
            self.lower_pov.close()

        self.upper_camera.close()
        self.lower_camera.close()
        self.mover.stop_moving()

    def _speaker(self):
        while not self.is_over:
            while self.speach_queue:
                text = self.speach_queue.pop()
                if text in ('hasta', 'tiger'):
                    file_id = self.player.loadFile(
                        '/home/nao/audio/' + text + '.mp3'
                    )
                    self.player.play(file_id)
                else:
                    self.tts.say(text)
            sleep(0.5)

    def _pov(self):
        while not self.is_over:
            try:
                self.upper_pov.get_frame()
                self.lower_pov.get_frame()
                sleep(0.1)
            except RuntimeError as e:
                print(e)
                continue

    def speak(self, text):
        if not self.speach_history or self.speach_history[-1] != text:
            self.speach_queue.appendleft(text)
            self.speach_history.append(text)

    def scan_rotation(self):
        """Intelligently rotate the robot to search for stuff."""
        self.mover.stop_moving()
        self.rotating = False
        yaw, pitch = self.mover.get_head_angles()

        # determine direction of head rotation
        sign = 1 if yaw >= 0 else -1

        # the robot starts to move arround his z-Axis in the direction where his
        # head is aligned when the head yaw angle has reached his maximum
        if yaw > pi/3:
            self.mover.set_head_angles(-pi / 8, pitch, 0.5)
            sleep(0.5)
        elif yaw < -pi/3:
            self.mover.move_to(0, 0, -pi / 4)
            self.mover.wait()
        # rotate head to the left, if head yaw angle is equally zero or larger
        # rotate head to the right, if head yaw angle is smaller than zero
        else:
            self.mover.change_head_angles(sign * pi / 8, 0, 0.5)
            sleep(0.3)

    def get_ball_angles_from_camera(self, cam, mask=True):
        """Detect the ball and return its angles in camera coordinates."""
        try:
            frame = cam.get_frame()
        except RuntimeError as e:  # Sometimes camera doesn't return an image
            print(e)
            return None

        if cam == self.lower_camera:
            mask = False

        if mask:
            field = self.field_finder.find(frame)
            frame = self.field_finder.mask_it(frame, field)
        ball = self.ball_finder.find(frame)

        if ball is None:
            return None

        (x, y), _ = ball
        x, y = cam.to_relative(x, y)
        x, y = cam.to_angles(x, y)
        return x, y

    def get_goal_angles_from_camera(self, cam, mask=True):
        try:
            frame = cam.get_frame()
        except RuntimeError as e:  # Sometimes camera doesn't return an image
            print(e)
            return None

        if mask:
            field = self.field_finder.find(frame)
            frame = self.field_finder.mask_it(frame, field, inverse=True)

        goal = self.goal_finder.find(frame)
        if goal is None:
            return None

        goal_l, goal_r = self.goal_finder.left_right_post(goal)
        goal_c = self.goal_finder.goal_center(goal)

        goal_l, _ = cam.to_relative(goal_l, 0)
        goal_l, _ = cam.to_angles(goal_l, 0)
        goal_r, _ = cam.to_relative(goal_r, 0)
        goal_r, _ = cam.to_angles(goal_r, 0)
        goal_c, _ = cam.to_relative(goal_c, 0)
        goal_c, _ = cam.to_angles(goal_c, 0)
        return goal_l, goal_r, goal_c

    def distance_to_ball(self):
        camera = 'upper'
        angles = self.get_ball_angles_from_camera(self.upper_camera)
        if angles is None:
            camera = 'lower'
            angles = self.get_ball_angles_from_camera(self.lower_camera)
            if angles is None:
                raise ValueError('No ball in sight')
        y_angle = angles[1]
        y_angle = pi/2 - y_angle - radians(16.5) - (radians(39)
                                                    if camera == 'lower'
                                                    else 0)
        print('Ball distance through', camera, 'camera')
        print('Angles', angles)
        return 0.5 * tan(y_angle)

    def walking_direction(self, lr, d, hypo):
        return (asin(0.43 / d) if hypo == 'bdist' else atan(0.23 / d)) * lr

    def ball_tracking(self, soll=0, tol=0.15):
        """Track the ball using the feed from top and bottom camera.

        Returns
        -------
        bool
            True if robot is nicely aligned to ball; else False.

        """

        ball_locked = False
        tried_step_back = False
        while not ball_locked:
            # visibility check
            for i in range(3):
                cams = [self.lower_camera, self.upper_camera]
                in_sight = False

                for cam in cams:
                    ball_angles = self.get_ball_angles_from_camera(cam)
                    if ball_angles is not None:
                        x, y = ball_angles
                        self._timer_start = time()
                        in_sight = True

                        break
                if in_sight:
                    break
            # stop visibility check

            if not in_sight:
                if not tried_step_back:
                    self.mover.move_to(-0.1, 0, 0)
                    self.mover.wait()
                    self.mover.stand_up()
                    tried_step_back = True
                else:
                    self.scan_rotation()
                continue

            ball_locked = self.turn_to_ball(x, y, soll=soll, tol=tol)
            print()

    def run_to_ball(self, d):
        self.mover.move_to(d, 0, 0)
        # self.mover.wait()

    def turn_to_ball(self, ball_x, ball_y, tol=0.15, soll=0):
        """Align robot to the ball.

        If head is not centered at the ball (within tolerance), then
        turn head to ball. If after that the angle of head to body
        becomes too big, rotate the body by the head angle and
        simultaneously rotate head into 0 position to achieve alignment.
        """

        # only the x ball angle is relevant for alignment
        d_yaw, d_pitch = ball_x, 0
        print('ball yaw in camera:', d_yaw)

        # center head at the ball
        if (abs(d_yaw) > 0.01):
            self.mover.change_head_angles(d_yaw, d_pitch,
                                          min(1, abs(d_yaw) * 1.25))
            sleep(0.1)

        head_yaw, head_pitch = self.mover.get_head_angles()
        self._timer_stop = time()
        print('Ball to head', self._timer_stop - self._timer_start)
        print('Head yaw', head_yaw, end=' ')
        d_yaw = head_yaw - soll
        print('Head d_yaw', d_yaw)
        print('Allowed tolerance', tol)

        if abs(d_yaw) > tol:
            self.mover.stop_moving()
            print('Going to rotate by', d_yaw)
            self.mover.set_head_angles(soll, head_pitch, 0.3)
            self.mover.move_to(0, 0, d_yaw)
            self.mover.wait()
            return False
        else:
            print('Ball locked')
            return True

    def align_to_ball(self):
        ball_angles = self.get_ball_angles_from_camera(self.lower_camera,
                                                       mask=False)
        if ball_angles is None:
            raise ValueError('No ball')
        x, y = ball_angles
        goal_x, goal_y = 0.092, 0.38
        dx, dy = goal_x - x, goal_y - y

        dx = -dx * 0.2 if abs(dx) > 0.03 else 0
        dy = dy * 0.3 if abs(dy) > 0.05 else 0
        if dx == 0  and dy == 0:
            return True
        print('Moving to dxdy', dx, dy)
        self.mover.move_to(dy, dx, 0)
        self.mover.wait()
        return False

    def align_to_goal(self):
        ball_angles = self.get_ball_angles_from_camera(self.lower_camera,
                                                       mask=False)
        if ball_angles is None:
            self.mover.move_to(-0.1, 0, 0)
            self.mover.wait()
            ball_angles = self.get_ball_angles_from_camera(self.lower_camera,
                                                           mask=False)
            if ball_angles is None:
                raise ValueError('No ball')
        x, y = ball_angles

        print(x, y)
        self.turn_to_ball(x, y, tol=0.15)
        sleep(0.2)

        goal = self.goal_search()
        if goal is None:
            return False

        gcl, gcr, gcc = goal
        print('Goal:', gcl, gcr, gcc)

        if gcl > 0.15 > -0.22 > gcr:
            return True

        if y > 0.38:
            self.mover.move_to(-0.05, 0, 0)
            self.mover.wait()
            # return False
        elif y < 0.28:
            self.mover.move_to(0.05, 0, 0)
            self.mover.wait()
            # return False

        sign = -1 if gcc > 0 else 1
        if sign == 1:
            self.speak('Goal is on the right')
        elif sign == -1:
            self.speak('Goal is on the left')

        for _ in range(2):
            self.mover.move_to(0, 0.05 * sign, 0)
            self.mover.wait()
        return False

    def goal_search(self):
        self.speak('Searching for goal')
        print('Last goal:', self.last_goal)
        goal_angles = None
        positions = [0, pi/6, pi/4, pi/3, pi/2]
        direction = 1 if self.last_goal == 'right' else -1
        angles = [-p for p in positions] + [p for p in positions][1:]
        angles = [a * direction for a in angles]

        for angle in angles:
            self.mover.set_head_angles(angle, -0.3)
            sleep(0.5)
            for i in range(5):
                print(i, goal_angles)
                goal_angles = self.get_goal_angles_from_camera(
                    self.upper_camera
                )
                if goal_angles is not None:
                    goal_angles = tuple(gc + angle for gc in goal_angles)
                    self.mover.set_head_angles(0, 0)
                    print('Goal found:', str(goal_angles))
                    self.last_goal = 'left' if goal_angles[2] > 0 else 'right'
                    return goal_angles
            print('Goal not found at ', str(angle))

        self.mover.set_head_angles(0, 0)
        return None
