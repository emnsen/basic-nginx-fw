#!/bin/bash

LOG_FILE="$1"
FILE="$2"
BEFORE_DATE_TIME=$(date --date='-5 minutes' +'%d/%b/%Y:%H:%M:00')
NOW_DATE_TIME=$(date +'%d/%b/%Y:%H:%M:00')
DATE=$(date +'%Y-%m-%d-%H-%M')

echo "Starting log filter. File: $LOG_FILE"
cat $FILE | awk -v d1="[$BEFORE_DATE_TIME" -v d2="[$NOW_DATE_TIME" '$4 >= d1 && $4 < d2' >> $LOG_FILE
echo "Finished log filter."
echo "Range: $BEFORE_DATE_TIME <==> $NOW_DATE_TIME"