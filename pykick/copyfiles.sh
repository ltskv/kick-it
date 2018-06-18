#!/bin/bash

# Exit immediately if something fails
set -e
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )"

if [ -z "$1" ]
then
    nao_ip=192.168.0.11
else
    nao_ip=$1
fi

destination="nao@$nao_ip:/home/nao/pykick/"

# copy the files with scp
scp "$repo/"*.py $destination
