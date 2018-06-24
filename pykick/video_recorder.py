# This test demonstrates how to use the ALVideoRecorder module.
# Note that you might not have this module depending on your distribution
import os
import sys
import time
from naoqi import ALProxy

# Replace this with your robot's IP address
IP = "192.168.0.11"
PORT = 9559

# Create a proxy to ALVideoRecorder
try:
  videoRecorderProxy = ALProxy("ALVideoRecorder", IP, PORT)
except Exception, e:
  print "Error when creating ALVideoRecorder proxy:"
  print str(e)
  exit(1)

videoRecorderProxy.setFrameRate(30.0)
videoRecorderProxy.setResolution(2) # Set resolution to VGA (640 x 480)
videoRecorderProxy.setCameraID(0)




# storage folder of the recording and the file name
videoRecorderProxy.startRecording("/home/nao/recordings/cameras", "camera1")

print "Video record started."

try:
	# set recording duration
    while True:
        pass

finally:
	videoInfo = videoRecorderProxy.stopRecording()
    
	#print "Video was saved on the robot: ", videoInfo[1]
	#print "Total number of frames: ", videoInfo[0]

	
