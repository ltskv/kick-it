import argparse

from .utils import read_config
from .movements import NaoMover


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        epilog='When called without arguments specifying the video source, ' +
        'will try to use the webcam'
    )
    parser.add_argument(
        '-f', '--foot',
        default='L',
        choices=['R', 'L']
    )
    args = parser.parse_args()

    cfg = read_config()
    mover = NaoMover(cfg['ip'])
    mover.stand_up()
    mover.kick(foot=args.foot)
