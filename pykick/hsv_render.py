"""Script explaining how HSV works."""

from __future__ import division, print_function

import sys

import cv2
import numpy as np


if __name__ == '__main__':
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    window = 'HSV Explained'
    h, s, v = 0, 255, 255

    print('u, i, o: increase h, s, v respectively',
          'j, k, l: decrease h, s, v respectively',
          '(focus on the image window for this and look at the terminal)',
          sep='\n')

    while True:
        image[:] = h, s, v
        im2show = cv2.cvtColor(image, cv2.COLOR_HSV2BGR)
        print(' HSV:', h, s, v, '      ', end='\r')
        sys.stdout.flush()
        cv2.imshow(window, im2show)
        key = cv2.waitKey(0)
        if key == ord('q'):
            break
        elif key == ord('u'):
            h = (h + 1) % 180
        elif key == ord('j'):
            h = (h - 1) % 180
        elif key == ord('i'):
            s = min(s + 1, 255)
        elif key == ord('k'):
            s = max(s - 1, 0)
        elif key == ord('o'):
            v = min(v + 1, 255)
        elif key == ord('l'):
            v = max(v - 1, 0)
