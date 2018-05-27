#!/bin/bash

# Exit if something fails
set -e

echo "Setting up sources.list"
sudo bash -c \
    'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" \
>/etc/apt/sources.list.d/ros-latest.list'

echo "Set up repository keys"
sudo apt-key adv \
    --keyserver hkp://ha.pool.sks-keyservers.net:80 \
    --recv-key 421C365BD9FF1F717815A3895523BAEEB01FA116

echo "Update packages list"
sudo apt update

echo "Install ROS"
sudo apt install ros-indigo-desktop -y

echo "Initialize rosdep"
sudo rosdep init
rosdep update

echo "Environment setup"
echo "source /opt/ros/indigo/setup.bash" >>${HOME}/.bashrc
source ${HOME}/.bashrc

echo "Get rosinstall"
sudo apt install python-rosinstall -y
