#!/bin/bash
/home/sielte/code/exec/rigman_0.1 -a 192.168.2.7 -p 9999 -stop
sleep 20
killall rigboot
killall runrig
killall camera
exit 0
