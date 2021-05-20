#!/bin/bash

if [ "$#" -ne 1 ]; then 
    echo "$0 <SERVER_NAME>"
	echo "$0 H1"
    exit 1
fi

filename="request_distribution_$1.log"

echo When you finish to test press Ctrl+C to show the stats
#Stop when find the HEAD request
bash mininet/util/m "$1" python3 -m http.server 80 > "$filename" 2>&1

file_lenght=$(cat "$filename" | wc -l)
lenght=$(($file_lenght - 3))

echo The number of requests received on this host are: $lenght