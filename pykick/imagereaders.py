from __future__ import division

import numpy as np
import cv2
try:
    from naoqi import ALProxy
except:
    ALProxy = None


class NaoImageReader(object):

    RESOLUTIONS = {
        0: (120, 160),
        1: (240, 320),
        2: (480, 640),
        3: (960, 1280)
    }

    def __init__(self, ip, port=9559, res=1, fps=30, cam_id=0, video_file=None):
        ip = bytes(ip)
        self.res_id = res
        self.recording = []
        self.res = self.RESOLUTIONS[res]
        self.video_file = video_file
        self.cam_id=cam_id
        self.fps = fps
        self.vd = ALProxy('ALVideoDevice', ip, port)
        streamer_name = '_'.join(['lower' if cam_id else 'upper', str(res)])
        self.sub = self.vd.subscribeCamera(
            streamer_name, cam_id, res, 13, fps
        )

    def to_angles(self, x, y):
        return self.vd.getAngularPositionFromImagePosition(
            self.cam_id, [x, y]
        )

    def to_relative(self, x, y):
        print('Camera resolution:', self.res)
        return x / self.res[1], y / self.res[0]

    def get_frame(self):
        result = self.vd.getImageRemote(self.sub)
        self.vd.releaseImage(self.sub)
        if result is None or result[6] is None:
            self.restart()
            raise RuntimeError(self.sub + " couldn't capture")
        else:
            height, width = self.res
            frame = np.frombuffer(result[6], dtype=np.uint8).reshape(
                height, width, 3
            )
            if self.video_file is not None:
                self.recording.append(frame)
            return frame

    def close(self):
        self.vd.unsubscribe(self.sub)
        print(self.sub + 'captured %s frames' % len(self.recording))
        print('Writing to', self.video_file)
        if self.video_file is not None:
            vf = cv2.VideoWriter(self.video_file,
                                 cv2.cv.FOURCC('X', 'V', 'I', 'D'),
                                 self.fps,
                                 (self.res[1], self.res[0]))
            for frame in self.recording:
                print('.')
                vf.write(frame)
            vf.release()

    def restart(self):
        self.vd.unsubscribe(self.sub)
        self.sub = self.vd.subscribeCamera(
            self.sub, self.cam_id, self.res_id, 13, self.fps
        )
        self.recording = []


class VideoReader(object):

    def __init__(self, filename=0, loop=False):
        self.cap = cv2.VideoCapture(filename)
        self.loop = loop if filename else False
        self.ctr = 0

    def get_frame(self):
        succ, frame = self.cap.read()
        if not succ:
            raise ValueError('Error while reading video.\n' +
                             'Or video is over.')
        self.ctr += 1
        if (self.ctr == self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT) and
            self.loop):
            self.ctr = 0
            self.cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, 0)
        return frame

    def close(self):
        self.cap.release()


class PictureReader(object):
    "Dummy class for maybe convenience."

    def __init__(self, filename):
        self.frame = cv2.imread(filename)

    def get_frame(self):
        return self.frame.copy()

    def close(self):
        pass
