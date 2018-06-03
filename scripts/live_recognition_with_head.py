from __future__ import print_function
from __future__ import division

#import imutils
from naoqi import ALProxy
from imagereaders import NaoImageReader
from live_recognition import BallFinder
from live_recognition_with_head_with_body import move_to


# Nao configuration
nao_ip = '192.168.0.11'
nao_port = 9559
#res = (3, (960, 1280))  # NAOQi code and acutal resolution
#res=(1,(240,320))
res=1
#res=(2,(480,640))

fps = 30
cam_id = 0  # 0 := top, 1 := bottom

# Recognition stuff
red_lower = (0, 185, 170)  # HSV coded red interval
red_upper = (6, 255, 255)
min_radius = 5
resized_width = None  # Maybe we need it maybe don't (None if don't)

current_value = 0
counter = 0

def get_angle():
    robotIP="192.168.0.11"
    PORT = 9559
    motionProxy = ALProxy("ALMotion", robotIP, PORT)
    names=["HeadPitch","HeadYaw"]
    useSensors=False
    angle=motionProxy.getAngles(names,useSensors)
    #print("angle_is"+str(angles))
    return angle

def set_angle_new(x,y):
    angle=get_angle()
    robotIP="192.168.0.11"
    PORT = 9559
    motionProxy = ALProxy("ALMotion", robotIP, PORT)

    # activiert gelenke
    motionProxy.setStiffnesses("Head", 0.5)
    names  = ["HeadYaw", "HeadPitch"]
    fractionMaxSpeed  = 0.3
    x_diff=x-0.5
    y_diff=y-0.5
    print("x_diff="+str(x_diff))
    print("y_diff="+str(y_diff))

    angles=[-x_diff / 2, 0]

    global counter
    if abs(x_diff) > 0.1:
        motionProxy.changeAngles(names, angles, fractionMaxSpeed)
        counter = 0
    else:
        counter += 1
        print(counter)
    if counter == 4:
        counter = 0
        print('Going to rotate')
        angle = get_angle()
        if abs(angle[1]) > 0.1:
            motionProxy.setStiffnesses("Head", 0.7)
            names  = ["HeadYaw", "HeadPitch"]
            fractionMaxSpeed  = 0.05
            angles=[0, 0]
            motionProxy.setAngles(names,angles,fractionMaxSpeed)
            move_to(0, 0, angle[1])
        move_to(0.3, 0, 0)


if __name__ == '__main__':
    video_top = NaoImageReader(nao_ip, port=nao_port, cam_id=0, res=res,
                               fps=fps)
    video_low = NaoImageReader(nao_ip, port=nao_port, cam_id=1, res=res,
                               fps=fps)
    finder = BallFinder(red_lower, red_upper, 5, None)
    finder.load_hsv_config('ball_hsv.json')
    try:
        while True:
            try:
                (x, y), radius = finder.find_colored_ball(video_top.get_frame())
                x, y = video_top.to_relative(x, y)
                print('Top camera')
            except TypeError:
                try:
                    (x, y), radius = finder.find_colored_ball(
                        video_low.get_frame()
                    )
                    x, y = video_low.to_relative(x, y)
                    print('Low camera')
                except TypeError:
                    continue
            print(x, y)
            print(x, y)
            set_angle_new(x,y)
    finally:
        video_top.close()
        video_low.close()
