from __future__ import print_function
from __future__ import division

from threading import Thread
from math import pi, cos, tan, asin, radians
from time import sleep, time, strftime
from collections import deque

from .utils import read_config
from .imagereaders import NaoImageReader
from .finders import BallFinder, GoalFinder, FieldFinder
from .movements import NaoMover
from naoqi import ALProxy


class Striker(object):

    VIDEO_FOLDER = '/home/nao/recordings/'

    def __init__(self, nao_ip, nao_port, res, ball_hsv, goal_hsv, field_hsv,
                 ball_min_radius):
        self.run_id = strftime('%Y%m%d%H%M%S')
        self.mover = NaoMover(nao_ip=nao_ip, nao_port=nao_port)
        self.mover.stand_up()
        self.upper_camera = NaoImageReader(nao_ip, port=nao_port, res=res,
                                           fps=30, cam_id=0)
        self.lower_camera = NaoImageReader(nao_ip, port=nao_port, res=res,
                                           fps=30, cam_id=1)
        self.ball_finder = BallFinder(tuple(ball_hsv[0]), tuple(ball_hsv[1]),
                                      ball_min_radius)
        self.field_finder = FieldFinder(tuple(field_hsv[0]),
                                        tuple(field_hsv[1]))
        self.goal_finder = GoalFinder(tuple(goal_hsv[0]), tuple(goal_hsv[1]))
        self.speaker = ALProxy('ALTextToSpeech', bytes(nao_ip), nao_port)
        self.recorder = ALProxy('ALVideoRecorder', bytes(nao_ip), nao_port)

        self.is_over = False

        self.speach_queue = deque(maxlen=4)
        self.tts_thread = Thread(target=self._speaker)
        self.tts_thread.start()

        self.rotating = False
        self.rot_dir = 0
        self.timer_start = 0
        self.timer_stop = 0
        self.dy = False

    def _speaker(self):
        while not self.is_over:
            while self.speach_queue:
                self.speaker.say(self.speach_queue.pop())
            sleep(0.1)

    def start_record(self, cam_id):
        if self.recorder.isRecording():
            print('Already recording. Please stop first')
            return
        self.recorder.setCameraID(cam_id)
        self.recorder.startRecording(self.VIDEO_FOLDER,
                                     'cam' + str(cam_id) + self.run_id)

    def stop_record(self):
        self.recorder.stopRecording()

    def speak(self, text):
        self.speach_queue.appendleft(text)

    def scan_rotation(self):
        """Intelligently rotate the robot to search for stuff."""
        self.mover.stop_moving()
        self.rotating = False
        yaw = self.mover.get_head_angles()[0]
        mag = yaw

        # determine direction of head rotation
        sign = 1 if yaw >= 0 else -1

        # the robot starts to move arround his z-Axis in the direction where his
        # head is aligned when the head yaw angle has reached his maximum
        if mag > 0.8:
            self.mover.set_head_angles(-pi / 8, 0, 0.5)
            sleep(0.5)
        elif mag < -0.8:
            self.mover.move_to_fast(0, 0, -pi / 4)
            self.mover.wait()
            #self.speak("Where is the ball? I am searching for it")
        # rotate head to the left, if head yaw angle is equally zero or larger
        # rotate head to the right, if head yaw angle is smaller than zero
        else:
            #self.speak("I have found the ball")
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

    def get_goal_center_angle_from_camera(self, cam, mask=True):
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

        goal_x = self.goal_finder.goal_center(goal)
        goal_x, _ = cam.to_relative(goal_x, 0)
        goal_x, _ = cam.to_angles(goal_x, 0)
        return goal_x

    def distance_to_ball(self):
        angles = self.get_ball_angles_from_camera(self.upper_camera)
        if angles == None:
            raise ValueError('No ball in sight')
        y_angle = angles[1]
        y_angle = pi/2 - y_angle - radians(15)
        return 0.5 * tan(y_angle)

    def walking_direction(self, lr, d):
        return asin(0.5 / d) * lr

    def ball_tracking(self, soll=0, tol=0.15):
        """Track the ball using the feed from top and bottom camera.

        Returns
        -------
        bool
            True if robot is nicely aligned to ball; else False.

        """

        ball_locked = False
        while not ball_locked:
            # visibility check
            for i in range(3):
                cams = [self.upper_camera, self.lower_camera]
                in_sight = False

                for cam in cams:
                    ball_angles = self.get_ball_angles_from_camera(cam)
                    if ball_angles is not None:
                        x, y = ball_angles
                        self.timer_start = time()
                        in_sight = True

                        break
                if in_sight:
                    break
            # stop visibility check

            if not in_sight:
                self.speak('No ball visible search it')
                self.scan_rotation()
                continue

            # self.speak('I see the ball')
            ball_locked = self.turn_to_ball(x, y, soll=soll, tol=tol)
            print()

    def run_to_ball(self, d):
        self.mover.move_to(d, 0, 0)
        self.mover.wait()

    def turn_to_ball(self, ball_x, ball_y, tol=0.15, soll=0, fancy=False,
                     m_delta=0.2):
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
        self.timer_stop = time()
        print('Ball to head', self.timer_stop - self.timer_start)
        print('Head yaw', head_yaw, end=' ')
        d_yaw = head_yaw - soll
        print('Head d_yaw', d_yaw)
        print('Rotating', self.rotating, end=' ')
        print('Rotation direction', self.rot_dir, end=' ')
        print('Allowed tolerance', tol)

        if not fancy:
            if abs(d_yaw) > tol:
                self.mover.stop_moving()
                print('Going to rotate by', d_yaw)
                self.speak('Going to rotate')
                self.mover.set_head_angles(soll, head_pitch, 0.3)
                self.mover.move_to(0, 0, d_yaw)
                self.mover.wait()
                return False
            else:
                print('Ball locked')
                return True

        else:
            if not self.rotating:
                if abs(d_yaw) > tol:
                    self.mover.stop_moving()
                    self.rotating = True
                    self.rot_dir = -1 if d_yaw > 0 else 1
                    print('Going to rotate')
                    self.speak("Going to rotate")
                    self.mover.move_toward(0, 0, -self.rot_dir)
                    # sleep(1.5)
                    return False
                else:
                    print('Success')
                    # self.speak('Ball locked')
                    return True
            else:
                if d_yaw * self.rot_dir > -tol - m_delta:
                    self.rotating = False
                    self.mover.stop_moving()
                return False

    def align_to_ball(self):
        ball_angles = self.get_ball_angles_from_camera(self.lower_camera,
                                                       mask=False)
        if ball_angles is None:
            raise ValueError('No ball')
        x, y = ball_angles
        goal_x, goal_y = 0.095, 0.30
        dx, dy = goal_x - x, goal_y - y

        dx = -dx * 0.2 if abs(dx) > 0.05 else 0
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
                self.speak("Cannot see the ball")
                raise ValueError('No ball')
        x, y = ball_angles

        print(x, y)
        self.speak("Turn to ball")
        self.turn_to_ball(x, y, tol=0.15)
        self.speak('Trying to find the goal')
        goal_center_x = self.goal_search()
        self.speak('Goal found')

        print('Goal center:', goal_center_x)
        if goal_center_x is not None and abs(goal_center_x) < 0.1:
            self.speak("Goal and ball are aligned")
            print('Goal ball aligned!')
            #raise SystemExit
            return True

        if y > 0.35:
            self.mover.move_to(-0.05, 0, 0)
            self.mover.wait()
            # return False
        elif y < 0.25:
            self.mover.move_to(0.05, 0, 0)
            self.mover.wait()
            # return False

        sign = -1 if goal_center_x > 0 else 1
        num_steps = int(min(abs(goal_center_x), 0.1) // 0.05)
        for _ in range(num_steps):
            self.mover.move_to(0, 0.05 * sign, 0)
            self.mover.wait()
        return False

    def close(self):
        self.is_over = True
        if self.tts_thread.isAlive():
            self.tts_thread.join()
        if self.recorder.isRecording():
            self.stop_record()
        self.upper_camera.close()
        self.lower_camera.close()
        self.mover.stop_moving()
        # self.mover.stand_up()

    def goal_search(self):
        goal_center_x = None
        positions = [0, pi/6, pi/4, pi/3, pi/2]
        angles = [-p for p in positions] + [p for p in positions][1:]
        for angle in angles:
            self.mover.set_head_angles(angle, 0)
            sleep(0.5)
            for i in range(5):
                print(i, goal_center_x)
                if goal_center_x is None:
                    gcx = self.get_goal_center_angle_from_camera(
                        self.upper_camera
                    )
                    goal_center_x = gcx + angle if gcx is not None else None
                    print('Goal found: ' + str(goal_center_x)
                          if goal_center_x is not None
                          else 'Goal not found at ' + str(angle))
            if goal_center_x is not None:
                self.mover.set_head_angles(0, 0)
                return goal_center_x
        self.mover.set_head_angles(0, 0)
        return None


# ____________________ STRIKER __________________________
#
#        +----> Ball tracking (see below) <-------------+
#        |                                              |
#        |               |                              |
#        |               |                              |
#        |               v                              |
#        |          Ball in lower cam?                  |
#        |              /  \                            |
#   lost |      yes    /    \ cannot do                 |
#   ball |            v      v                          |
#        +-- Goal align    Ball is only in top camera --+
#                |              Move closer.
#                |
#     successful |
#                v
#             Kick it! (Fancy or simple)
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

    try:  # Hit Ctrl-C to stop, cleanup and exit
        cfg = read_config()
        striker = Striker(
            nao_ip=cfg['ip'], nao_port=cfg['port'],
            res=cfg['res'], ball_hsv=cfg['ball'],
            goal_hsv=cfg['goal'], field_hsv=cfg['field'],
            ball_min_radius=cfg['ball_min_radius'],
        )

        state = 'init'
        init_soll = 0.0
        align_start = 0.15
        curve_start = -0.1
        curve_stop = 0.1
        soll = init_soll
        while True:
            # meassure time for debbuging
            loop_start = time()
            print('State:', state)

            if state == 'init':
                striker.start_record(0)
                striker.mover.set_head_angles(0, 0)
                striker.ball_tracking(tol=0.05)
                # goal_center = striker.goal_search()
                # approach = 1 if goal_center < 0 else -1
                approach = 1
                state = 'ball_approach'

            elif state == 'tracking':
                # start ball approach when ball is visible
                print('Soll angle')
                striker.ball_tracking(tol=0.05)
                break
                # state = 'ball_approach'

            elif state == 'ball_approach':
                # bil = striker.get_ball_angles_from_camera(
                    # striker.lower_camera
                # )  # Ball in lower

                # print('Ball in lower', bil)
                try:
                    d = striker.distance_to_ball()
                except ValueError:
                    state = 'tracking'
                    continue
                print('Distance to ball', d)
                angle = striker.walking_direction(approach, d)
                d_run = d * cos(angle)
                print('Approach angle', angle)
                striker.mover.move_to(0, 0, angle)
                striker.mover.wait()
                striker.run_to_ball(d_run)
                striker.mover.move_to(0, 0, -pi/2 * approach)
                state = 'tracking'

            elif state == 'goal_align':
                try:
                    if striker.align_to_goal():
                        striker.speak('I am aligning to ball')
                        state = "align"
                except ValueError:
                        state = 'tracking'

            elif state == 'align':
                striker.stop_record()
                striker.start_record(1)
                striker.mover.set_head_angles(0, 0.25, 0.3)
                sleep(0.5)
                try:
                    success = striker.align_to_ball()
                    sleep(0.3)
                    if success:
                        striker.speak('I am going. To kick ass')
                        state = 'kick'
                except ValueError:
                    pass
                    # striker.mover.set_head_angles(0, 0, 0.3)
                    # state = 'tracking'

            elif state == 'simple_kick':
                striker.mover.set_head_angles(0,0.25,0.3)
                striker.ball_tracking(tol=0.10, soll=0)
                print('Doing the simple kick')

                # just walk a short distance forward, ball should be near
                # and it will probably be kicked in the right direction
                striker.speak("Simple Kick")
                sleep(1)
                striker.mover.move_to_fast(0.5, 0, 0)
                striker.mover.wait()
                break
                # state = 'tracking'

            elif state == 'kick':
                print('KICK!')
                striker.mover.stand_up()
                sleep(0.3)
                striker.mover.kick(fancy=True, foot='L')
                break

            loop_end = time()
            print('Loop time:', loop_end - loop_start)
            print('\n\n')
    finally:
        striker.close()
        striker.mover.rest()
