from __future__ import print_function
from __future__ import division

import json
from imagereaders import NaoImageReader, VideoReader
from finders import BallFinder


if __name__ == '__main__':
    video = VideoReader(0, loop=True)
    with open('ball_hsv.json') as f:
        hsv = json.load(f)
    hsv_lower = tuple(map(hsv.get, ('low_h', 'low_s', 'low_v')))
    hsv_upper = tuple(map(hsv.get, ('high_h', 'high_s', 'high_v')))
    finder = BallFinder(hsv_lower, hsv_upper, 5, None)
    try:
        while True:
            frame = video.get_frame()
            finder.find_colored_ball(frame)
            finder.visualize(frame)
    finally:
        video.close()
