# Kicker project

## Prerequisites

1. (L)ubuntu 14.04 32-bit
2. Git installed:

```sh
sudo apt install git -y 
```

## How to start working

1. Install the software:

```sh
cd ~/Documents
git clone https://gitlab.lrz.de/robocupss18-blue3/kick-it.git
cd kick-it
setup/install_ros.sh
setup/install_nao_ros.sh
```

2. Check if ROS is working properly by typing `roscore` and finishing it with
`ctrl-c` if it doesn't throw errors.

3. Check if NAOQi binding for Python works by launching Python and running there
`from naoqi import ALProxy`. The installation was successful if it imports
without errors. You can finish Python with `ctrl-d` then.
