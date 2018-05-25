#!/bin/sh
echo "Setting up sources.list"
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
sleep 1
echo "Set up your keys"
sudo apt-key adv --keyserver hkp://ha.pool.sks-keyservers.net:80 --recv-key 421C365BD9FF1F717815A3895523BAEEB01FA116
sleep 1

echo "Doing apt update"
sudo apt update
sleep 1

echo "installing ros"
#sudo apt-get install ros-indigo-desktop-full
sudo apt-get install ros-indigo-desktop 
sleep 1

echo "Initialize rosdep"
sudo rosdep init
sleep 1
rosdep update
sleep 1

echo "Environment setup"
echo "source /opt/ros/indigo/setup.bash" >> ~/.bashrc
sleep 1
source ~/.bashrc

sleep 1
echo "getting rosinstall"
sudo apt install python-rosinstall 



exit 0
