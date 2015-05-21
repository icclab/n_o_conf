#!/bin/bash

case $1 in
 --help | -h)
  echo "Usage: check_ram [warn] [crit]"
  echo " [warn] and [crit] as int"
  echo " Example: check_ram 20 10"
  exit 3
  ;;

 *)
  ;;

esac

warn=$1
crit=$2

if [ ! "$1" -o ! "$2" ]; then
 echo "Usage: check_ram [warn] [crit]"
 echo " [warn] and [crit] as int"
 echo " Example: check_ram 20 10"
 echo "Unknown: Options missing: using default (warn=20, crit=10)"
 warn=`echo $((20))`
 crit=`echo $((10))`
fi

free=`free -m | grep 'Mem:' | awk '{print $4}'`
full=`free -m | grep 'Mem:' | awk '{print $2}'`


if [ "$warn" -lt "$crit" -o "$warn" -eq "$crit" ]; then
 echo "Unknown: [warn] must be larger than [crit]"
 exit 3
fi

use=`echo $(( ($free * 100) / $full ))`

if [ "$use" -gt "$warn" -o "$use" -eq "$warn" ]; then
 echo "OK: $use % free memory"
 exit 0
elif [ "$use" -lt "$warn" -a "$use" -gt "$crit" ]; then
 echo "Warning: $use % free memory"
 exit 1
elif [ "$use" -eq "$crit" -o "$use" -lt "$crit" ]; then
 echo "Critical: $use % free memory"
 exit 2
else
 echo "Unknown"
 exit 3
fi
