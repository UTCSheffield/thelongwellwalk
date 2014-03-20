#!/bin/bash
#Installer

sudo apt-get update
sudo apt-get upgrade

#Do GPS install described here
#http://www.stuffaboutcode.com/2013/09/raspberry-pi-gps-setup-and-python.html

sudo apt-get install gpsd gpsd-clients python-gps ddclient python-picamera python3-picamera rsync unison ppp usb-modeswitch wvdial python-alsaaudio

mkdir /home/pi/BPOA/

#do ssh-copy-id 
