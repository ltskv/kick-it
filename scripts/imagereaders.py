import numpy as np
import cv2
from naoqi import ALProxy


class NaoImageReader(object):

    RESOLUTIONS = {
        1: (240, 320),
        2: (480, 640),
        3: (960, 1280)
    }

    def __init__(self, ip, port=9559, res=1, fps=30, cam_id=0):
        self.res = self.RESOLUTIONS[res]
        self.vd = ALProxy('ALVideoDevice', ip, port)
        self.sub = self.vd.subscribeCamera(
            "video_streamer", cam_id, res, 13, fps
        )

    def get_frame(self):
        result = self.vd.getImageRemote(self.sub)
        self.vd.releaseImage(self.sub)
        if result == None:
            raise RuntimeError('cannot capture')
        elif result[6] == None:
            raise ValueError('no image data string')
        else:
            height, width = self.res
            return np.frombuffer(result[6], dtype=np.uint8).reshape(
                height, width, 3
            )

    def close(self):
        self.vd.unsubscribe(self.sub)


class VideoReader(object):

    def __init__(self, filename=0, loop=False):
        self.cap = cv2.VideoCapture(filename)
        self.loop = loop if filename else False
        self.ctr = 0

    def get_frame(self):
        succ, frame = self.cap.read()
        if not succ:
            raise ValueError('Error while reading video')
        self.ctr += 1
        if self.ctr == self.cap.get(cv2.CAP_PROP_FRAME_COUNT) and self.loop:
            self.ctr = 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        return frame

    def close(self):
        self.cap.release()
