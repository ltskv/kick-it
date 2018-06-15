from .utils import read_config
from .movements import NaoMover


if __name__ == "__main__":
    cfg = read_config()
    mover = NaoMover(cfg['ip'])
    mover.stand_up()
    mover.kick(foot="R")
    mover.stand_up()
