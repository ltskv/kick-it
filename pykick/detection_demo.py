from __future__ import print_function
from __future__ import division

from .utils import read_config
from .imagereaders import NaoImageReader, VideoReader
from .finders import BallFinder


if __name__ == '__main__':
    video = VideoReader(0, loop=True)
    cfg = read_config()
    hsv_lower = cfg['red'][0]
    hsv_upper = cfg['red'][1]
    finder = BallFinder(hsv_lower, hsv_upper, cfg['min_radius'], None)
    try:
        while True:
            frame = video.get_frame()
            finder.find_colored_ball(frame)
            finder.visualize(frame)
    finally:
        video.close()
