#!/bin/bash
/opt/miniconda3/bin/python /home/sielte/code/rig-dev/src/rigman/main.py -c /home/sielte/code/conf/conf_dev.json -stop
sleep 20
killall rigboot
killall runrig
killall rigcam
exit 0

