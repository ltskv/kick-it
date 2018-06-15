from naoqi import ALProxy
from time import sleep
# create proxy on ALMemory
memProxy = ALProxy("ALMemory",'192.168.0.11',9559)


while 1:
#get data. Val can be int, float, list, string
	val = memProxy.getData("Device/SubDeviceList/Head/Temperature/Sensor/Value")
	print(val)
	sleep(1)

#print(val)
