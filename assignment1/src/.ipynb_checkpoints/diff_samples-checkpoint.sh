#!/bin/bash

usage () {
    echo "usage: diff_samples.sh data_dir " 1>&2
    exit 1
}

if [ $# -ne 1 ] || [ ! -d $d ]; then
    usage
fi

#Dataset directory
DATA_DIR=$1

SCENAIROS=$( ls $DATA_DIR )
for SCENARIO in $SCENAIROS; do
    RUNS="$( ls $DATA_DIR/$SCENARIO )"
    for RUN in $RUNS; do
        CASES="$CASES $SCENARIO/$RUN"
    done
done


#getting logs warns errors and wins 
if [ ! -d logs_wew ]; then
    mkdir logs_wew
fi

for CASE in $CASES; do
    N_CASE=$(echo $CASE | sed -E "s#/#_#")
    echo "#logs warns errors and wins" > logs_wew/logs_wew_$N_CASE
    for LOG in $(find $DATA_DIR/$CASE/logs/ -maxdepth 1 -type f); do
        if egrep -q "ERROR|WARN|goal" $LOG;then
            echo "$LOG" >> logs_wew/logs_wew_$N_CASE
            egrep "ERROR|WARN|goal" $LOG >> logs_wew/logs_wew_$N_CASE
            echo "" >> logs_wew/logs_wew_$N_CASE
        fi
    done
done
