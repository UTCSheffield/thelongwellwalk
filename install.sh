#!/bin/bash
#Installer

sudo apt-get update
sudo apt-get -y upgrade

#Do GPS install described here
#http://www.stuffaboutcode.com/2013/09/raspberry-pi-gps-setup-and-python.html

sudo apt-get -y install gpsd gpsd-clients python-gps python-picamera python3-picamera rsync unison ppp usb-modeswitch wvdial python-alsaaudio

#sudo apt-get -y install ddclient

##sudo cp cmdline.txt  /boot/cmdline.txt
##sudo cp inittab /etc/inittab

#sudo gpxlogger -d -m 10 -f filename.gpx

mkdir /home/pi/BPOA/

#do ssh-copy-id 
