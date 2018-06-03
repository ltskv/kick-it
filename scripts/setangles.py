import argparse
from motion import NaoMover
from utils import read_config


if __name__ == "__main__":

    cfg = read_config()
    parser = argparse.ArgumentParser()
    parser.add_argument('yaw', type=float)
    parser.add_argument('pitch', type=float)
    parser.add_argument('speed', type=float, nargs='?', default=0.1)
    args = parser.parse_args()

    mover = NaoMover(cfg['ip'], cfg['port'])
    mover.set_head_angles(args.yaw, args.pitch, args.speed)
