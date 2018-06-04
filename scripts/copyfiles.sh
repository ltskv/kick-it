#!/bin/bash

# Exit immediately if something fails
set -e


if [ -z "$1" ] 
then
	nao_ip=192.168.0.11
else
	nao_ip=$1
fi

sshpass -p 'nao' ssh nao@$nao_ip 'cd ~ && rm ball_approach.py utils.py finders.py movements.py imagereaders.py || echo "already removed"'


# copy the files with scp
sshpass -p 'nao' scp ball_approach.py  nao@$nao_ip:~
sshpass -p 'nao' scp utils.py  nao@$nao_ip:~
sshpass -p 'nao' scp finders.py  nao@$nao_ip:~
sshpass -p 'nao' scp movements.py  nao@$nao_ip:~
sshpass -p 'nao' scp imagereaders.py nao@$nao_ip:~



# config ersetzen
#sshpass -p 'nao' scp nao_defaults.json   nao@192.168.0.11:~

