from .movements import NaoMover
from .utils import read_config


if __name__ == "__main__":
    cfg = read_config()
    mover = NaoMover(cfg['ip'], cfg['port'])
    mover.stand_up()
    while True:
        amount = float(raw_input('How much: '))
        mover.move_to(0, 0, 0.5 * amount)
        mover.wait()
        mover.move_to(0, -0.3 * amount, 0)
        mover.wait()
        mover.move_to(-0.1 * abs(amount), 0, 0)
        # amount = float(raw_input('How much: '))
        # if axis == 0:
            # mover.move_to(amount, 0, 0)
        # elif axis == 1:
            # mover.move_to(0, amount, 0)
        # elif axis == 2:
            # mover.move_to(0, 0, amount)
        # else:
            # print('Axis out of range (0, 1, 2)')
