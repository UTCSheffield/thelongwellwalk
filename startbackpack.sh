#!/bin/bash
sudo gpsd -n /dev/ttyAMA0 -F /var/run/gpsd.sock
while :
do
	sudo python /home/pi/thelongwellwalk/backpack.py
done
