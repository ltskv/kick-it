from __future__ import print_function
from __future__ import division

import argparse

import cv2

from .utils import read_config, imresize, field_mask
from .imagereaders import NaoImageReader, VideoReader, PictureReader
from .finders import BallFinder, GoalFinder, FieldFinder


if __name__ == '__main__':
    defaults = read_config()
    parser = argparse.ArgumentParser()
    # parser.add_argument(
        # '-i', '--input-config',
        # help='file, from which to read the initial values',
        # required=True
    # )
    imsource = parser.add_mutually_exclusive_group()
    imsource.add_argument(
        '--video-file',
        help='video file to use'
    )
    imsource.add_argument(
        '--image-file',
        help='image to use'
    )
    imsource.add_argument(
        '--nao-ip',
        help='ip address of the nao robot, from which to capture',
        default=False,
        const=defaults['ip'],
        nargs='?'
    )
    parser.add_argument(
        '--still',
        help='only take one image from video stream',
        action='store_true'
    )
    parser.add_argument(
        '--manual',
        help='switch frames manually',
        action='store_true',
        default=False
    )

    parser.add_argument(
        '--nao-cam',
        choices=[0, 1],
        type=int,
        help='0 for top camera, 1 for bottom camera',
        default=defaults['cam']
    )
    parser.add_argument(
        '--nao-res',
        choices=[1, 2, 3],
        help='choose a nao resolution',
        type=int,
        default=defaults['res']
    )
    parser.add_argument(
        '--width',
        help='specify width of the image output',
        type=int,
        default=640
    )
    args = parser.parse_args()

    if args.video_file:
        rdr = VideoReader(args.video_file, loop=True)
    elif args.image_file:
        rdr = PictureReader(args.image_file)
    elif args.nao_ip:
        rdr = NaoImageReader(
            args.nao_ip,
            cam_id=args.nao_cam,
            res=args.nao_res
        )
    else:
        rdr = VideoReader(0)

    goal_finder = GoalFinder(defaults['goal'][0], defaults['goal'][1])
    ball_finder = BallFinder(defaults['ball'][0], defaults['ball'][1],
                             defaults['ball_min_radius'])
    field_finder = FieldFinder(defaults['field'][0], defaults['field'][1])
    ball_window = 'Ball detection'
    goal_window = 'Goal detection'
    cv2.namedWindow(ball_window)
    cv2.namedWindow(goal_window)

    try:
        if args.still:
            frame = rdr.get_frame()
            rdr.close()
        while True:
            if not args.still:
                frame = rdr.get_frame()
            frame = imresize(frame, width=args.width)

            field = field_finder.find(frame)
            not_field = cv2.bitwise_not(field)

            ball_frame = field_finder.draw(frame, field)
            goal_frame = field_finder.draw(frame, not_field)

            ball = ball_finder.find(ball_frame)
            goal = goal_finder.find(goal_frame)

            ball_frame = ball_finder.draw(ball_frame, ball)
            goal_frame = goal_finder.draw(goal_frame, goal)

            cv2.imshow(ball_window, ball_frame)
            cv2.imshow(goal_window, goal_frame)

            key = cv2.waitKey(0 if args.manual else 1)
            if key == ord('q') or key == 27:
                break
    finally:
        if not args.still:
            rdr.close()
