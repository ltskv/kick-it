import argparse
import cv2
from datetime import datetime
from utils import read_config
from imagereaders import NaoImageReader


if __name__ == '__main__':
    cfg = read_config()
    parser = argparse.ArgumentParser()
    parser.add_argument('--res', type=int, choices=(1, 2, 3),
                        default=3)
    parser.add_argument('--cam-id', type=int, choices=(0, 1),
                        default=0)
    args = parser.parse_args()

    video = NaoImageReader(cfg['ip'], res=args.res, cam_id=args.cam_id,
                           fps=1)
    frame = video.get_frame()
    video.close()
    now = datetime.now().strftime('%Y%m%d%H%M%S')

    prefix = 'bottom' if args.cam_id else 'top'
    cv2.imwrite(prefix + now + '.jpg', frame)
