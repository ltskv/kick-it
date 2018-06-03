import argparse
from motion import NaoMover
from utils import read_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('state', choices=('stand', 'rest'))
    args = parser.parse_args()
    cfg = read_config()
    mover = NaoMover(cfg['ip'], cfg['port'])
    if args.state == 'stand':
        mover.stand_up()
    elif args.state == 'rest':
        mover.rest()
