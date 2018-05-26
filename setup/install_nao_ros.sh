#!/bin/bash

# Exit immediately if something fails
set -e

# opt is better that $HOME imho
naoqi_root='/opt/naoqi'
pynaoqi='pynaoqi-python2.7-2.1.4.13-linux32'
cppnaoqi='naoqi-sdk-2.1.4.13-linux32'

echo "Make NAOQi root dir"
sudo mkdir ${naoqi_root}
cd ${naoqi_root}

echo "Get the SDKs"
sudo wget \
    'https://drive.google.com/uc?export=download&id=1cZYzD_kK-Ty3n7cqYcX1M7XMOSAs899O' \
    -O "pynaoqi.tar.gz"

sudo wget \
    'https://drive.google.com/uc?export=download&id=1qmT2GiRJ5icZkWScjKqCIErIevu8fLkF' \
    -O "cppnaoqi.tar.gz"

sudo tar xzf cppnaoqi.tar.gz && sudo rm cppnaoqi.tar.gz
sudo tar xzf pynaoqi.tar.gz && sudo rm pynaoqi.tar.gz

echo "Add the NAOqi library path to PYTHONPATH"
export PYTHONPATH="${naoqi_root}/${pynaoqi}:$PYTHONPATH"

echo "Make this permanently available for every future terminal"
echo 'export PYTHONPATH="'"${naoqi_root}/${pynaoqi}"':$PYTHONPATH"' \
    >>${HOME}/.profile

echo "Install ROS packages for Nao"
sudo apt-get install ros-indigo-nao-robot
