from __future__ import print_function, division

from time import time, sleep
from math import cos, pi

from .striker import Striker
from .utils import read_config, InterruptDelayed


if __name__ == '__main__':

    try:  # Hit Ctrl-C to stop, cleanup and exit
        cfg = read_config()
        with InterruptDelayed():
            striker = Striker(
                nao_ip=cfg['ip'], nao_port=cfg['port'],
                res=cfg['res'], ball_hsv=cfg['ball'],
                goal_hsv=cfg['goal'], field_hsv=cfg['field'],
                ball_min_radius=cfg['ball_min_radius'],
            )
            print('Initialized')
            striker.mover.stand_up()

        state = 'init'
        # init_soll = 0.0
        # align_start = 0.15
        # curve_start = -0.1
        # curve_stop = 0.1
        # soll = init_soll
        striker.speak("Initialized")
        approach_steps = 0
        loop_start = time()
        while True:
            loop_end = time()
            print('Loop time:', loop_end - loop_start)
            print('\n\n')

            # meassure time for debbuging
            loop_start = time()
            print('State:', state)

            if state == 'init':
                striker.mover.set_head_angles(0, 0)
                striker.speak("Start the Ball tracking")
                striker.ball_tracking(tol=0.05)
                striker.speak(
                    "I have found the Ball, starting with. Goal search"
                )
                _, _, gcc = striker.goal_search()

                if abs(gcc) < 0.4:
                    striker.speak('Direct approach')
                    state = 'straight_approach'
                    approach = 0
                    continue

                if gcc < 0:
                    striker.speak("I have found the. goal on the right")
                    approach = 1
                else:
                    striker.speak("I have found the. goal on the left")
                    approach = -1

                striker.mover.set_head_angles(0, 0)
                #approach = 1 if goal_center < 0 else -1
                #approach = 1
                sleep(0.5)
                state = 'ball_approach'

            elif state == 'tracking':
                # start ball approach when ball is visible
                print('Soll angle')
                striker.ball_tracking(tol=0.15)
                # break
                if approach_steps < 2 and approach != 0:
                    state = 'ball_approach'
                else:
                    state = 'straight_approach'

            elif state == 'straight_approach':
                bil = striker.get_ball_angles_from_camera(
                    striker.lower_camera
                )  # Ball in lower
                print('Ball in lower!', bil)
                if bil is not None and bil[1] > 0.15:
                    striker.speak('Ball is close enough, stop approach')
                    striker.mover.stop_moving()
                    striker.speak('Align to goal')
                    state = 'goal_align'
                else:
                    striker.speak('Continue running')
                    striker.run_to_ball(1)
                    state = 'tracking'

            elif state == 'ball_approach':
                sleep(0.8)
                bil = striker.get_ball_angles_from_camera(
                    striker.lower_camera
                )  # Ball in lower

                try:
                    d = striker.distance_to_ball()
                except ValueError:
                    if bil is not None:
                        state = 'straight_approach'
                        striker.speak('Ball is close. ' +
                                      'But not close enough maybe')
                    else:
                        state = 'tracking'
                    continue

                print('Distance to ball', d)
                striker.speak("The distance to the ball is approximately "
                              + str(round(d,2)) + " Meters")
                angle = striker.walking_direction(approach, d)
                d_run = d * cos(angle)
                print('Approach angle', angle)

                striker.mover.move_to(0, 0, angle)
                striker.mover.wait()
                striker.run_to_ball(d_run)
                striker.mover.wait()
                striker.speak("I think I have reached the ball. " +
                              "I will start rotating")
                approach_steps += 1
                striker.mover.move_to(0, 0, -pi/2 * approach)
                striker.mover.wait()
                state = 'tracking'

            elif state == 'goal_align':
                try:
                    if striker.align_to_goal():
                        state = "align"
                except ValueError:
                        state = 'tracking'

            elif state == 'align':
                striker.speak("I will try now to align to the ball")
                striker.mover.set_head_angles(0, 0.25, 0.3)
                sleep(0.5)
                try:
                    success = striker.align_to_ball()
                    sleep(0.3)
                    if success:
                        striker.speak('Hasta la vista, Baby')
                        state = 'kick'
                except ValueError:
                    pass
                    # striker.mover.set_head_angles(0, 0, 0.3)
                    # state = 'tracking'

            elif state == 'simple_kick':
                striker.mover.set_head_angles(0,0.25,0.3)
                striker.ball_tracking(tol=0.10, soll=0)
                print('Doing the simple kick')

                # just walk a short distance forward, ball should be near
                # and it will probably be kicked in the right direction
                striker.speak("Simple Kick")
                sleep(1)
                striker.mover.move_to_fast(0.5, 0, 0)
                striker.mover.wait()
                break

            elif state == 'kick':
                print('KICK!')
                striker.mover.stand_up()
                sleep(0.3)
                striker.mover.kick(fancy=True, foot='L')
                striker.mover.stand_up()
                sleep(2)
                striker.speak("Nice kick. Let's do a dance")
                striker.mover.dance()
                break
    finally:
        striker.close()
        striker.mover.rest()


# ____________________ STRIKER __________________________
#
#        +----> Ball tracking (see below) <-------------+
#        |                                              |
#        |               |                              |
#        |               |                              |
#        |               v                              |
#        |          Ball in lower cam?                  |
#        |              /  \                            |
#   lost |      yes    /    \ cannot do                 |
#   ball |            v      v                          |
#        +-- Goal align    Ball is only in top camera --+
#                |              Move closer.
#                |
#     successful |
#                v
#             Kick it! (Fancy or simple)
#
# _______________________________________________________

# ____________________ TRACKING _________________________
#
#                        yes
# check if ball visible ---> rotate head to the ball
#     ^            |                    |
#     |            | no                 |
#     |            v                    |
#     +--- ball scan rotation           |
#     |                                 |
#     |                  no             V
#     |               +---------- already rotating body?
#     |               |                 |
#     |               v                 | yes
#     |       head angle too big?       v
#     |             /  \            head angle
#     |        yes /    \ no     is below threshold?
#     |           v      v              |         |
#     |        stop    successful       | no      | yes
#     |       moving      exit          |         v
#     +----- and start                  |    stop rotating body
#     |    rotating body                |         |
#     |                                 |         |
#     +---------------------------------+---------+
#
# _______________________________________________________
