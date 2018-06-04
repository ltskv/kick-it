from naoqi import ALProxy


class NaoMover(object):

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

    def stand_up(self):
        self.set_arm_stiffness(0.9)
        self.set_hand_stiffness(0.9)
        self.pp.goToPosture('StandInit', 1.0)
        self.set_hand_stiffness()
        self.set_arm_stiffness()

    def rest(self):
        self.mp.rest()
        self.ready_to_move = False

    def set_head_stiffness(self, stiffness=0.8):
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

    def set_hip_stiffness(self, stiffness=0.9):
        self.mp.setStiffnesses("LHipYawPitch", stiffness)
        self.mp.setStiffnesses("LHipPitch", stiffness)
        self.mp.setStiffnesses("RHipYawPitch", stiffness)
        self.mp.setStiffnesses("RHipPitch", stiffness)
        self.mp.setStiffnesses("LHipRoll", stiffness)
        self.mp.setStiffnesses("RHipRoll", stiffness)

    def set_ankle_stiffness(self, stiffness=0.9):
        self.mp.setStiffnesses("LAnklePitch", stiffness)
        self.mp.setStiffnesses("LAnkleRoll", stiffness)
        self.mp.setStiffnesses("RAnklePitch", stiffness)
        self.mp.setStiffnesses("RAnkleRoll", stiffness)

    def set_knee_stiffness(self, stiffness=0.9):
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
