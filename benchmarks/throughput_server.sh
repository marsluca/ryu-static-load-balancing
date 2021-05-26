#!/bin/bash

if [ "$#" -ne 1 ]; then 
    echo "$0 <SERVER_NAME>"
	echo "$0 SRV1"
    exit 1
fi

/home/vagrant/mininet/util/m "$1" netserver &