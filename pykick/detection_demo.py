from __future__ import print_function
from __future__ import division

import argparse

import cv2

from .utils import read_config, imresize, field_mask
from .imagereaders import NaoImageReader, VideoReader, PictureReader
from .finders import BallFinder, GoalFinder


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
                             defaults['min_radius'])
    window_name = 'Live detection'
    cv2.namedWindow(window_name)

    try:
        if args.still:
            frame = rdr.get_frame()
            rdr.close()
        while True:
            if not args.still:
                frame = rdr.get_frame()
            frame = imresize(frame, width=args.width)
            field_hsv = defaults['field']
            field = field_mask(frame, field_hsv[0], field_hsv[1])
            not_field = cv2.bitwise_not(field)
            goal = goal_finder.find_goal_contour(
                cv2.bitwise_and(frame, frame, mask=not_field))
            ball = ball_finder.find_colored_ball(
                cv2.bitwise_and(frame, frame, mask=field))
            goal_finder.draw(frame, goal)
            ball_finder.draw(frame, ball)
            cv2.imshow(window_name, frame)

            key = cv2.waitKey(0 if args.manual else 1)
            if key == ord('q') or key == 27:
                break
    finally:
        if not args.still:
            rdr.close()
