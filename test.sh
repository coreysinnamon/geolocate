#!/bin/bash

# ping and traceroute
DATE=`date '+%Y-%m-%d %H:%M:%S'`
echo "Date: $DATE" > outputsh.txt

while IFS='' read -r LINE || [[ -n "$LINE" ]]
    do
        echo -e "$LINE"
        echo -e "$LINE\n" >> outputsh.txt
        TIME=`date +%s`
        echo -e "Time: $TIME" >> outputsh.txt
        IP=`echo "$LINE" | sed 's/, .*//'`
        ping "$IP" -c 10 >> outputsh.txt
        echo -e "\n" >> outputsh.txt
        echo -e "Tracing route to $IP.\n" >> outputsh.txt
        sudo traceroute "$IP" >> outputsh.txt
        echo -e "Traceroute complete.\n" >> outputsh.txt
        echo -e "\n\n" >> outputsh.txt
done < targets.txt
