#!/bin/bash

pwd=$(pwd)
newline='
'

if [ "$#" -ne 2 ]; then 
    echo "$0 <CLIENT_NAME> <SERVER_IP>"
	echo "$0 h1 10.0.1.3"
    exit 1
fi

n_conn="1 10 100 500 1000"

mkdir -p tests/throughput
cd tests/throughput

for N in $n_conn; do
	echo "Inizio test con $N connessioni..."
	/home/vagrant/mininet/util/m $1 flent tcp_1down --test-parameter=download_streams=$N --no-annotation -p box_totals -l 60 -H $2 --figure-dpi=150 --figure-note=" " --bounds-y 0,1000 --bounds-y 0,10 -t "Throughput_Benchmark$newline" -o out_$N.png
done

sudo chown -R vagrant "$pwd"
