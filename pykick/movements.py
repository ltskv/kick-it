# from time import sleep
import argparse
from math import radians, pi

from naoqi import ALProxy

from .utils import read_config

class NaoMover(object):

    KICK_SEQUENCE = [

        # lean to the side using the ankle joints
        [[(0, 1, 'ShoulderRoll', -70),
          (0 , 1, 'AnkleRoll', -9),
          (1 , 1 , 'AnkleRoll', -9)], 0.3],

        # perform the fast kick
        [[(1, 0, 'HipPitch', -45),
          (1, 0, 'AnklePitch', 10),
          (1, 0, 'KneePitch', 10)], 0.15],

        # bring knee back for better kick recovery
        [[(1, 0, 'KneePitch', 40)], 0.2]
    ]

    # fancy kick
    KICK_SEQUENCE_FANCY = [
        # base_or_kicking, unsymmetric, joint, angle

        # lift the arm
        [[(0, 1, 'ShoulderRoll', -70)], 0.5],

        # lean to the side using the ankle joints
        [[(0, 1, 'AnkleRoll', -10),
          (1, 1, 'AnkleRoll', -10)],
         1],

        # lift the foot using the knee joint and the ankle joint
        [[(1, 0, 'KneePitch', 90),
          (1, 0, 'AnklePitch', -40)],
         0.7],

        # kick-it!
        [[(1, 0, 'HipPitch', -45),
          (1, 0, 'KneePitch', 10),
          (1, 0, 'AnklePitch', 0)],
         0.3],

        # prepare to return into standing position
        [[(1, 0, 'KneePitch', 40),
          (1, 0, 'AnklePitch', 10)],
         0.5],
    ]


    def __init__(self, nao_ip, nao_port=9559):
        nao_ip = bytes(nao_ip)
        self.mp = ALProxy('ALMotion', nao_ip, nao_port)
        self.pp = ALProxy('ALRobotPosture', nao_ip, nao_port)
        ap = ALProxy("ALAutonomousLife", nao_ip, nao_port)
        if ap.getState() != "disabled":
            ap.setState('disabled')
        self.set_head_stiffness()
        self.set_hand_stiffness()
        self.set_arm_stiffness()
        self.set_hip_stiffness()
        self.set_knee_stiffness()
        self.set_ankle_stiffness()
        self.ready_to_move = False

    def kick(self, foot='L', fancy=False):
        self.set_arm_stiffness(0.8)
        self.set_hip_stiffness(0.8)
        self.set_knee_stiffness(0.8)
        self.set_ankle_stiffness(1)
        if foot == 'L':
            sides = ['R', 'L']
        elif foot == 'R':
            sides = ['L', 'R']
        kick_sequence = (self.KICK_SEQUENCE_FANCY if fancy
                         else self.KICK_SEQUENCE)
        for motion, wait in kick_sequence:
            joints = []
            angles = []
            for part in motion:
                print(part)
                side, unsymmetric, joint, angle = part
                if foot == 'R' and unsymmetric:
                    angle *= -1
                joints.append(sides[side] + joint)
                angles.append(radians(angle))
            self.mp.angleInterpolation(joints, angles, wait, True)

        self.stand_up(0.5)
        self.set_arm_stiffness()
        self.set_hip_stiffness()
        self.set_knee_stiffness()
        self.set_ankle_stiffness()

    def stand_up(self, speed=0.8):
        self.set_arm_stiffness(0.9)
        self.set_hand_stiffness(0.9)
        self.pp.goToPosture('StandInit', speed)
        self.set_hand_stiffness()
        self.set_arm_stiffness()

    def rest(self):
        self.mp.rest()
        self.ready_to_move = False

    def set_head_stiffness(self, stiffness=0.5):
        self.mp.setStiffnesses("Head", stiffness)

    def set_hand_stiffness(self, stiffness=0.0):
        self.mp.setStiffnesses("RHand", stiffness)
        self.mp.setStiffnesses("LHand", stiffness)
        self.mp.setStiffnesses("LWristYaw", stiffness)
        self.mp.setStiffnesses("RWristYaw", stiffness)

    def set_arm_stiffness(self, stiffness=0.3):
        self.mp.setStiffnesses("LShoulderPitch", stiffness)
        self.mp.setStiffnesses("LShoulderRoll", stiffness)
        self.mp.setStiffnesses("LElbowRoll", stiffness)
        self.mp.setStiffnesses("LElbowYaw", stiffness)
        self.mp.setStiffnesses("RShoulderPitch", stiffness)
        self.mp.setStiffnesses("RShoulderRoll", stiffness)
        self.mp.setStiffnesses("RElbowRoll", stiffness)
        self.mp.setStiffnesses("RElbowYaw", stiffness)

    def set_hip_stiffness(self, stiffness=0.6):
        self.mp.setStiffnesses("LHipYawPitch", stiffness)
        self.mp.setStiffnesses("LHipPitch", stiffness)
        self.mp.setStiffnesses("RHipYawPitch", stiffness)
        self.mp.setStiffnesses("RHipPitch", stiffness)
        self.mp.setStiffnesses("LHipRoll", stiffness)
        self.mp.setStiffnesses("RHipRoll", stiffness)

    def set_ankle_stiffness(self, stiffness=0.6):
        self.mp.setStiffnesses("LAnklePitch", stiffness)
        self.mp.setStiffnesses("LAnkleRoll", stiffness)
        self.mp.setStiffnesses("RAnklePitch", stiffness)
        self.mp.setStiffnesses("RAnkleRoll", stiffness)

    def set_knee_stiffness(self, stiffness=0.6):
        self.mp.setStiffnesses("LKneePitch", stiffness)
        self.mp.setStiffnesses("RKneePitch", stiffness)

    def get_head_angles(self):
        return self.mp.getAngles(('HeadYaw', 'HeadPitch'), False)

    def change_head_angles(self, d_yaw, d_pitch, speed=0.5):
        self.mp.changeAngles(('HeadYaw', 'HeadPitch'),
                             (d_yaw, d_pitch), speed)

    def change_head_angles_blocking(self, d_yaw, d_pitch, speed=0.5):
        self.mp.angleInterpolatioWithSpeed(('HeadYaw', 'HeadPitch'),
                                           (d_yaw, d_pitch), speed, False)

    def set_head_angles(self, yaw, pitch, speed=0.5):
        self.mp.setAngles(('HeadYaw', 'HeadPitch'),
                          (yaw, pitch), speed)

    def set_head_angles_blocking(self, yaw, pitch, speed=0.5):
        self.mp.angleInterpolatioWithSpeed(('HeadYaw', 'HeadPitch'),
                                           (yaw, pitch), speed, True)

    def move_to(self, front, side, rotation, wait=False):
        if not self.ready_to_move:
            self.mp.moveInit()
            self.ready_to_move = True
        if rotation != 0:
            n_cycles = int(abs(rotation) // (pi/4))
            sign = 1 if rotation > 0 else -1
            rest = abs(rotation) % (pi/4)
            print('Rotation', rotation, 'Cycles', n_cycles, 'Rest', rest)
            for _ in range(n_cycles):
                self.mp.post.moveTo(0, 0, pi/4 * sign)
                self.wait()
            self.mp.post.moveTo(0, 0, rest * sign)
        else:
            self.mp.post.moveTo(front, side, rotation)

    def move_to_fast(self, front, side, rotation, wait=False):
        if not self.ready_to_move:
            self.mp.moveInit()
            self.ready_to_move = True
        self.mp.post.moveTo(front, side, rotation, [
                ['MaxStepX', 0.07999999821186066],
                ['MaxStepY', 0.1599999964237213],
                ['MaxStepTheta', 0.5235987901687622],
                ['MaxStepFrequency', 1.0],
                ['StepHeight', 0.02]
        ])

    def move_toward(self, front, side, rotation):
        if not self.ready_to_move:
            self.mp.moveInit()
            self.ready_to_move = True
        self.mp.post.moveToward(front, side, rotation)

    def dance(self):
        dance_sequence = [[["LLeg"], [[0.06, 0.1, 0.0]]],
                         [["LLeg"], [[0.00, 0.16, 0.0]]],
                         [["RLeg"], [[0.00, -0.1, 0.0]]],
                         [["LLeg"], [[0.00, 0.16, 0.0]]],
                         [["RLeg"], [[-0.04, -0.1, 0.0]]],
                         [["RLeg"], [[0.00, -0.16, 0.0]]],
                         [["LLeg"], [[0.00, 0.1, 0.0]]],
                         [["RLeg"], [[0.00, -0.16, 0.0]]]]

        step_frequency = 0.8
        clear_existing = False
        cycles = 2 # defined the number of cycle to make

        for _ in range(cycles):
            for leg, positions in dance_sequence:
                self.mp.setFootStepsWithSpeed(
                    leg, positions, (step_frequency,),
                    clear_existing
                )
        self.wait()
        self.stand_up(0.7)

    def wait(self):
        self.mp.waitUntilMoveIsFinished()

    def stop_moving(self):
        print('STOOOP')
        self.mp.stopMove()


if __name__ == '__main__':
    cfg = read_config()
    mover = NaoMover(cfg['ip'], cfg['port'])
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("-s", "--stand", action="store_true",
                        help="let the robot stand up")
    actions.add_argument("-k", "--kick", action="store_true",
                        help="let the robot do a fancy kick")
    actions.add_argument("-r", "--rest", action="store_true",
                        help="let the robot rest")
    actions.add_argument("-m", "--move", action="store_true",
                        help="move around")
    actions.add_argument("-d", "--dance", action="store_true",
                        help="blow up the dance floor")

    args = parser.parse_args()

    if args.stand:
        mover.stand_up()

    elif args.rest:
        mover.rest()

    # perform a (fancy) kick
    elif args.kick:
        mover.stand_up()
        mover.kick(fancy=True)

    elif args.move:
        mover.stand_up()
        while True:
            amount_x = float(raw_input('How much x: '))
            amount_y = float(raw_input('How much y: '))
            amount_z = float(raw_input('How much z: '))
            print(amount_x, amount_y, amount_z)
            mover.move_to(amount_x, amount_y, amount_z)
            mover.wait()

    elif args.dance:
        mover.stand_up()
        mover.dance()
