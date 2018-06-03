from __future__ import print_function
from __future__ import division

import json
import argparse
import cv2
from imagereaders import VideoReader, NaoImageReader, PictureReader
# import imutils

class Colorpicker(object):

    WINDOW_CAPTURE_NAME = 'Video Capture'
    WINDOW_DETECTION_NAME = 'Object Detection'

    def __init__(self):
        parameters = ['low_h', 'low_s', 'low_v', 'high_h', 'high_s', 'high_v']
        maxes = [180, 255, 255, 180, 255, 255]
        checkers = [
            lambda x: min(x, self.settings['high_h'] - 1),  # LOW H
            lambda x: min(x, self.settings['high_s'] - 1),  # LOW S
            lambda x: min(x, self.settings['high_v'] - 1),  # LOW H
            lambda x: max(x, self.settings['low_h'] + 1),  # HIGH H
            lambda x: max(x, self.settings['low_s'] + 1),  # HIGH S
            lambda x: max(x, self.settings['low_v'] + 1),  # HIGH V
        ]
        self.settings = {
            'low_h': 0,
            'low_s': 0,
            'low_v': 0,
            'high_h': 180,
            'high_s': 255,
            'high_v': 255
        }
        cv2.namedWindow(self.WINDOW_CAPTURE_NAME)
        cv2.namedWindow(self.WINDOW_DETECTION_NAME)
        self.trackers = [
            cv2.createTrackbar(
                name, self.WINDOW_DETECTION_NAME, self.settings[name], max_v,
                lambda val, name=name, checker=checker: self._on_trackbar(
                    val, name, checker
                )
            )
            for name, max_v, checker in zip(parameters, maxes, checkers)
        ]

    def do_print(self):
        print(self.settings)

    def _on_trackbar(self, val, name, checker):
        self.settings[name] = checker(val)
        cv2.setTrackbarPos(name, self.WINDOW_DETECTION_NAME,
                           self.settings[name])

    def show_frame(self, frame, width=None):
        frame_HSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame_threshold = cv2.inRange(
            frame_HSV,
            tuple(map(self.settings.get, ('low_h', 'low_s', 'low_v'))),
            tuple(map(self.settings.get, ('high_h', 'high_s', 'high_v')))
        )
        if width:
            sf = width / frame.shape[1]
            frame = cv2.resize(frame, (0, 0), fx=sf, fy=sf)
            frame_threshold = cv2.resize(frame_threshold, (0, 0), fx=sf, fy=sf)
        cv2.imshow(self.WINDOW_CAPTURE_NAME, frame)
        cv2.imshow(self.WINDOW_DETECTION_NAME, frame_threshold)
        return cv2.waitKey(1)

    def save(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def load(self, filename):
        with open(filename) as f:
            self.settings = json.load(f)
        for name in self.settings:
            cv2.setTrackbarPos(name, self.WINDOW_DETECTION_NAME,
                               self.settings[name])


if __name__ == '__main__':

    with open('nao_defaults.json') as f:
        defaults = json.load(f)

    parser = argparse.ArgumentParser(
        epilog='When called without arguments specifying the video source, ' +
        'will try to use the webcam'
    )
    parser.add_argument(
        '-o', '--output-config',
        help='file, to which the settings will be saved (if given)'
    )
    parser.add_argument(
        '-i', '--input-config',
        help='file, from which to read the initial values'
    )
    imsource = parser.add_mutually_exclusive_group()
    imsource.add_argument(
        '--video-file',
        help='video file to use'
    )
    imsource.add_argument(
        '--image-file',
        help='image to use'
    )
    imsource.add_argument(
        '--nao-ip',
        help='ip address of the nao robot, from which to capture',
        default=False,
        const=defaults['ip'],
        nargs='?'
    )
    parser.add_argument(
        '--still',
        help='only take one image from video stream',
        action='store_true'
    )
    parser.add_argument(
        '--nao-cam',
        choices=[0, 1],
        help='0 for top camera, 1 for bottom camera',
        default=defaults['cam']
    )
    parser.add_argument(
        '--nao-res',
        choices=[1, 2, 3],
        help='choose a nao resolution',
        type=int,
        default=defaults['res']
    )
    parser.add_argument(
        '--width',
        help='specify width of the image output',
        type=int,
        default=640
    )
    args = parser.parse_args()

    cp = Colorpicker()
    if args.input_config:
        cp.load(args.input_config)

    if args.video_file:
        rdr = VideoReader(args.video_file, loop=True)
    elif args.image_file:
        rdr = PictureReader(args.image_file)
    elif args.nao_ip:
        rdr = NaoImageReader(
            args.nao_ip,
            cam_id=args.nao_cam,
            res=args.nao_res
        )
    else:
        rdr = VideoReader(0)

    try:
        if args.still:
            frame = rdr.get_frame()
            rdr.close()
        while True:
            if not args.still:
                frame = rdr.get_frame()
            key = cp.show_frame(frame, args.width)
            if key == ord('q') or key == 27:
                break
    finally:
        cp.do_print()
        if args.output_config:
            cp.save(args.output_config)
        if not args.still:
            rdr.close()
