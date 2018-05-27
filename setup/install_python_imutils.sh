#!/bin/bash

# Exit if something fails
set -e

echo "Install Python-pip"
sudo apt install python-pip -y

echo "Install imutils"
sudo pip install imutils
