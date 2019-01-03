#!/bin/bash

FILE="$1"
echo "IP's Blocking..."
#while read line; do echo "$line"; done < $FILE
while read line; do /sbin/ipset -exist add blacklist $line; echo "IP: $line"; done < $FILE
echo "IP's BLocked"