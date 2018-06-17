#!/bin/bash

# Exit immediately if something fails
set -e

if [ -z "$1" ]
then
    nao_ip=192.168.0.11
else
    nao_ip=$1
fi

destination="$nao_ip:/home/nao/pykick/"

# copy the files with scp
scp -v striker.py utils.py finders.py \
    movements.py imagereaders.py $destination
