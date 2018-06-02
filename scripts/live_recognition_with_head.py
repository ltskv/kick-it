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

    # videoProxy=ALProxy('ALVideoDevice', robotIP, PORT)
    # ball_angles=videoProxy.getAngularPositionFromImagePosition(cam_id,[x/320,y/240])
    # print(ball_angles)
    # ball_angle_x=ball_angles[0]
    # ball_angle_y=ball_angles[1]
    # print("ball_angle_x="+str(ball_angle_x))
    # print("ball_angle_y="+str(ball_angle_y))

    # ball_angle_x_diff=ball_angle_x+
    # ball_angle_y_diff=ball_angle_y-99
    # print(ball_angle_x_diff*3.14/180)
    # print(ball_angle_y_diff)

    # print(ball_angles-[-169,99])
    # [-169.53343200683594, 99.27782440185547] (x_mid,y_mid)
    # if abs(ball_angle_x)>0.2 and abs(ball_angle_y)>0.01:
    # angles=[ball_angle_x,0]
    # angles=[0.25*ball_angle_x,0.25*ball_angle_y]
    # angles=[0.25*ball_angle_x,0.25*ball_angle_y]
    # angles=[2*(-1 if x_diff > 0 else 1),2*(-1 if y_diff > 0 else 1)]
    angles=[-x_diff / 2, 0]

    #if abs(ball_angle_x)>0.1 or abs(ball_angle_y)>0.1:
    #if abs(x_diff)>50 or abs(y_diff)>50:
    global counter
    if abs(x_diff) > 0.1:
        motionProxy.changeAngles(names, angles, fractionMaxSpeed)
        counter = 0
    else:
        counter += 1
        print(counter)
    if counter == 10:
        print('Going to rotate')
        angle = get_angle()
        if abs(angle[1]) > 0.1:
            move_to(0, angle[1])
            #motionProxy.setAngles(names,angles,fractionMaxSpeed)
    #else:
    #        a=get_angle()
    #        motionProxy.setAngles(names,a,fractionMaxSpeed)

    '''
    elif abs(ball_angle_x)<0.1 and abs(ball_angle_y)<0.1:
            #tts = ALProxy("ALTextToSpeech", "192.168.0.11", 9559)
            #tts.setParameter("pitchShift", 1)
            #tts.setParameter("speed", 50)
            #tts.setVoice("Kenny22Enhanced")

            #tts.say("Ball found")
            global counter
            counter=counter+1
	    #print(counter)
	    #print("Ball found")
            if counter==5:
		    global counter
                    counter=0
	            print(get_angle())

     '''

def set_angle(direction):
#def main(robotIP,x,y):
    robotIP="192.168.0.11"
    PORT = 9559
    motionProxy = ALProxy("ALMotion", robotIP, PORT)
    # activiert gelenke
    motionProxy.setStiffnesses("Head", 1.0)
    
    
    #names         = "HeadYaw"
    #useSensors    = False
    
    #commandAngles = motionProxy.getAngles(names, useSensors)

    #type(commandAngles)
    #type(float(commandAngles))
    #current_angle=float(commandAngles)
    #print(current_angle)
    #next_angle=float(commandAngles)-0.2
    #print("next_angle"+str(next_angle))
        #angles  = [0,next_angle]


    
    #print("set_angle")
    # Example showing how to set angles, using a fraction of max speed
    names  = ["HeadYaw", "HeadPitch"]
    #global current_value
    a=get_angle()
    #print(a[0])
#    print(a)
       
    
    #current_value=current_value-0.2
    if direction=="up":
        angles  = [a[1],a[0]-0.2]
    elif direction=="down":
	angles = [a[1], a[0]+0.2]    
    elif direction=="right":
        angles= [a[1]-0.2,a[0]]
    elif direction=="left":
	angles=[a[1]+0.2,a[0]]
    fractionMaxSpeed  = 0.5
    
    motionProxy.setAngles(names, angles, fractionMaxSpeed)


if __name__ == '__main__':
    video = NaoImageReader(nao_ip, port=nao_port, cam_id=cam_id, res=res,
                           fps=fps)
    finder = BallFinder(red_lower, red_upper, 5, None)
    finder.load_hsv_config('ball_hsv.json')
    try:
        while True:
            try:
                (x, y), radius = finder.find_colored_ball(video.get_frame())
            except TypeError:
                continue
            print(x, y)
            x, y = video.to_relative(x, y)
            print(x, y)
            set_angle_new(x,y)
            '''
 	    if 0<y<100:
                set_angle("up")
            elif 240>y>200:
                set_angle("down")
            if 0<x<100:  # maybe do simultaneous x-y setting
                set_angle("left")
            elif 320>x>220:
                set_angle("right")
  	    '''
    finally:
        video.close()
