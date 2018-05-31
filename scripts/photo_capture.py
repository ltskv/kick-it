import numpy as np
import cv2
from naoqi import ALProxy
from datetime import datetime

nao_ip = '192.168.0.11'
nao_port = 9559
res = (3, (960, 1280))  # NAOQi code and acutal resolution
fps = 1

# get NAOqi module proxy

# select camer
# 0: Top
# 1: Bottom
camera=0

videoDevice = ALProxy('ALVideoDevice', nao_ip, nao_port)
subscriber = videoDevice.subscribeCamera(
    "tester", camera, res[0], 13, fps
)
# create image
image = np.zeros((res[1][0], res[1][1], 3), np.uint8)

for k in range(1):

    result = videoDevice.getImageRemote(subscriber)
    videoDevice.releaseImage(subscriber)

    now = datetime.now().strftime('%Y%m%d%H%M%S')
    if result == None:
        print 'cannot capture.'
    elif result[6] == None:
        print 'no image data string.'
    else:
        values = map(ord, list(result[6]))
        i = 0
        for y in range(res[1][0]):
            for x in range(res[1][1]):
                image.itemset((y, x, 0), values[i + 0])
                image.itemset((y, x, 1), values[i + 1])
                image.itemset((y, x, 2), values[i + 2])
                i += 3
    if camera==0:
        cv2.imwrite('top' + now + '.jpg', image)
    else:
        cv2.imwrite('bottom' + now + '.jpg',image)
    

videoDevice.unsubscribe(subscriber)
