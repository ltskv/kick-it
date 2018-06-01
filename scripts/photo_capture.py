import cv2
from datetime import datetime
from imagereaders import NaoImageReader
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--res', type=int, choices=(1, 2, 3),
                        default=3)
    parser.add_argument('--cam-id', type=int, choices=(0, 1),
                        default=0)
    args = parser.parse_args()

    video = NaoImageReader('192.168.0.11', res=args.res, cam_id=args.cam_id,
                           fps=1)
    frame = video.get_frame()
    video.close()
    now = datetime.now().strftime('%Y%m%d%H%M%S')

    prefix = 'bottom' if args.cam_id else 'bottom'
    cv2.imwrite(prefix + now + '.jpg', frame)
