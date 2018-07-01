from __future__ import print_function, division

from time import time, sleep
from math import cos, pi

from .striker import Striker
from .utils import read_config, InterruptDelayed


if __name__ == '__main__':

    try:  # Hit Ctrl-C to stop, cleanup and exit
        cfg = read_config()
        with InterruptDelayed():  # Ignore Ctrl-C for a while
            striker = Striker(
                nao_ip=cfg['ip'], nao_port=cfg['port'],
                res=cfg['res'], ball_hsv=cfg['ball'],
                goal_hsv=cfg['goal'], field_hsv=cfg['field'],
                ball_min_radius=cfg['ball_min_radius'],
            )

            # striker.speak('tiger')
            # sleep(4.75)
            striker.mover.stand_up(1.0)
            # sleep(9)
            # print('Initialized')
        striker.speak('Initialized')

        state = 'init'
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
                striker.ball_tracking(tol=0.05)
                striker.mover.stand_up()
                sleep(0.5)
                bdist = striker.distance_to_ball()
                striker.speak('Ball distance is %.2f' % bdist)
                _, _, gcc = striker.goal_search()
                print('Goal center', gcc, 'Ball dist', bdist)

                if abs(gcc) < 0.2 or bdist <= 0.35:
                    print('Straight approach')
                    state = 'straight_approach'
                    approach = 0

                elif 0.35 < bdist < 0.50:
                    print('Rdist is hypo')
                    state = 'rdist_is_hypo'
                    approach = 1 if gcc < 0 else - 1
                else:
                    print('Bdist is hypo')
                    state = 'bdist_is_hypo'
                    approach = 1 if gcc < 0 else - 1

                if approach == 1:
                    striker.speak('Goal on the right')
                elif approach == -1:
                    striker.speak('Goal on the left')
                else:
                    striker.speak('Direct approach')

                striker.mover.set_head_angles(0, 0)
                sleep(0.5)

            elif state == 'straight_approach':
                striker.ball_tracking(tol=0.20)
                bil = striker.get_ball_angles_from_camera(
                    striker.lower_camera
                )  # Ball in lower print('Ball in lower!', bil)
                if bil is not None and bil[1] > 0.20:
                    striker.mover.stop_moving()
                    striker.speak('Ball is close enough. Aligning to goal')
                    state = 'goal_align'
                else:
                    striker.run_to_ball(1)

            elif state == 'bdist_is_hypo':
                angle = striker.walking_direction(approach, bdist, 'bdist')
                rdist = bdist * cos(angle)
                print('Approach angle', angle, 'Run distance', rdist)

                striker.mover.move_to(0, 0, angle)
                striker.mover.wait()
                if rdist > 1.5:
                    striker.run_to_ball(1.5)
                    striker.mover.wait()
                else:
                    striker.run_to_ball(rdist)
                    striker.mover.wait()
                    striker.mover.move_to(0, 0, -pi/2 * approach)
                    striker.mover.wait()
                state = 'init'

            elif state == 'rdist_is_hypo':
                angle = striker.walking_direction(approach, bdist, 'rdist')
                rdist = bdist / cos(angle)
                print('Approach angle', angle, 'Run distance', rdist)

                striker.mover.move_to(0, 0, angle)
                striker.mover.wait()
                striker.run_to_ball(rdist)
                striker.mover.wait()
                striker.mover.move_to(0, 0, (-pi/2 - angle) * approach)
                striker.mover.wait()
                state = 'init'

            elif state == 'goal_align':
                try:
                    if striker.align_to_goal():
                        striker.speak('Ball and goal are aligned')
                        state = "align"
                except ValueError:
                    continue

            elif state == 'align':
                striker.mover.set_head_angles(0, 0.25, 0.3)
                sleep(0.5)
                try:
                    success = striker.align_to_ball()
                    sleep(0.3)
                    if success:
                        state = 'kick'
                        # striker.speak('hasta')
                except ValueError:
                    striker.ball_tracking()

            elif state == 'kick':
                print('KICK!')
                striker.mover.stand_up()
                sleep(0.3)
                striker.mover.kick(fancy=True, foot='L')
                striker.mover.stand_up()
                striker.mover.set_head_angles(0, 0)
                striker.speak('Trying to confirm the goal')
                sleep(3)
                ball = striker.get_ball_angles_from_camera(striker.upper_camera)
                goal = striker.goal_search()

                if ball is not None and goal is not None:
                    ball_x = ball[0]
                    gcl, gcr, _ = goal
                    print('Ball, goal', ball, goal)
                    if not (gcl > ball_x > gcr):
                        striker.speak('I Failed')
                        sleep(0.5)
                        break
                    else:
                        striker.speak('I succeeded, confirmed')
                        sleep(0.5)
                        break

                striker.speak('I succeeded, presumably')
                striker.mover.stand_up()
                sleep(0.5)
                # striker.speak('Nice kick. Lets do the dance')
                # sleep(2)
                # striker.mover.dance()
                break
    finally:
        striker.close()
        striker.mover.rest()


#  _________________________ STRIKER _____________________________
# [                                                               ]
# [  Ball tracking --> Distance to ball --> Goal angle            ]
# [    ^                                           |              ]
# [    |                                           |              ]
# [    |                                yes        v              ]
# [    |                  Ball distance <--  Goal angle > thr     ]
# [    |                 /   |         \           |              ]
# [    |        > 50 cm /    |(35,50)   \ < 35cm   | no           ]
# [    |               /     v           \         v              ]
# [    +- Distance is <   Walk is hypo    \  Straight approach    ]
# [    |    hypo              |            >  until goal align    ]
# [    |                      |                (bil > 0.2)        ]
# [    -----------------------+                    |              ]
# [                                                |              ]
# [      | / |  /^ | /                             v              ]
# [      |(  | (   |(       Ball           Goal align             ]
# [      | \ |  \_ | \ <-- align <-- (if lost ball run backwards) ]
# [_______________________________________________________________]
