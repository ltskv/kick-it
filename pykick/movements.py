from time import sleep
from math import radians

from naoqi import ALProxy


class NaoMover(object):

    KICK_SEQUENCE = [
        # base_or_kicking, unsymmetric, joint, angle, speed

        [[(0, 1, 'ShoulderRoll', -70, 0.025)], 1],

        [[(0, 1, 'AnkleRoll', -10, 0.05),
          (1, 1, 'AnkleRoll', -10, 0.05)],
         2],

        [[(1, 0, 'KneePitch', 90, 0.05),
          (1, 0, 'AnklePitch', -40, 0.05)],
         3,],

        [[(1, 0, 'HipPitch', -45, 0.08),
          (1, 0, 'KneePitch', 10, 0.20),
          (1, 0, 'AnklePitch', 20, 0.16)],
         4]
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

    def kick(self, foot='L'):
        self.set_arm_stiffness(0.8)
        self.set_hip_stiffness(0.8)
        self.set_knee_stiffness(0.8)
        self.set_ankle_stiffness(0.8)
        multiplier = 4
        if foot == 'L':
            sides = ['R', 'L']
        elif foot == 'R':
            sides = ['L', 'R']
        for motion, wait in self.KICK_SEQUENCE:
            for part in motion:
                print(part)
                side, unsymmetric, joint, angle, speed = part
                if foot == 'R' and unsymmetric:
                    angle *= -1
                self.mp.setAngles(
                    [sides[side] + joint], [radians(angle)], speed * multiplier
                )
            sleep(wait)

        self.stand_up()

    def stand_up(self):
        self.set_arm_stiffness(0.9)
        self.set_hand_stiffness(0.9)
        self.pp.goToPosture('StandInit', 1.0)
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

    def change_head_angles(self, d_yaw, d_pitch, speed):
        self.mp.changeAngles(('HeadYaw', 'HeadPitch'),
                             (d_yaw, d_pitch), speed)

    def set_head_angles(self, yaw, pitch, speed):
        self.mp.setAngles(('HeadYaw', 'HeadPitch'),
                              (yaw, pitch), speed)

    def move_to(self, front, side, rotation, wait=False):
        if not self.ready_to_move:
            self.mp.moveInit()
            self.ready_to_move = True
        self.mp.post.moveTo(front, side, rotation)

    def wait(self):
        self.mp.waitUntilMoveIsFinished()
