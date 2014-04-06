#!/usr/bin/python
# Raspberry Pi based system for recording and transmitting data from a lone long distance walker.
# Being built for http://thelongwellwalk.org/

#Import the supporting code we need
import picamera         # Controlling the Camera
import time             # Time and Date functions
import os               # Operating system information and functions
import io               # Input and Output (Files and streams))
import RPi.GPIO as GPIO # Controls the GPIO for LEDs and Buttons
import sys
from GPSController import *
import math
import getopt
import subprocess

#Config
#tl_target = 60          # How long between each Timelapse shot
tl_target = 20          # How long between each Timelapse shot
buffer_length = 15      # How many seconds worth of video do we keep in the buffer
debug = True            # Do we print out debugging messages
f_favail_limit = 20000  # How much disk space is too little space (measured in blocks)

arecordcmd = "arecord -D plughw:1,0 "
# TODO : use the --max-file-time on the audio files

duration_step = 1
duration_timelapse = 60

next_step = 1
next_timelapse = 60

cycle_wait = 0.10

poweroffclicktarget = 6
poweroffclickstep = 2
powerclickcount = 0

videosizelimit = 20000
audiosizelimit = 10000
sizewarning    = 50000

loadavglimit = 1.25

#Where are files stored
outputbasedir =  os.path.expanduser('/home/pi/BPOA/')

#GPIO Config
# Which GPIO pin does what job
videobutton = 11        # Video (currently rigged as momentary switch) 
audiobutton = 12        # Audio (no code so far)
poweroffbutton = 12        # Poweroff button (can be same as audio)

statusLED_R = 18          # Red LED, short wire on own
statusLED_G = 16          # Green LED middle length wire
statusLED_B = 15          # Blue LED short wire next to middle length
#The GND wire is the longest and is wired through a switch so it only shows when pressed

GPS_TXD     = 8
GPS_RXD     = 10

# Status variables
videorecording = False  # Are we currently recording video
audiorecording = False  # Are we currently recording audio
tl_count  = 55          # Starting Timelapse count 55 means it will take 5 seconds to do first timlapse
loadlimitbreached = False
videosizelimitreached = False
audiosizelimitreached = False
sizewarningreached = False
transferring = False


# Functions

# Work out the file name based on the current time and file type
def getFileName(curtime, ext):
    name = time.strftime("%Y-%m-%d-%H-%M-%S", curtime)+"."+ext
    return name

# Work out the file folder based on the current time and file type
def getFolderName(curtime, ext):
    name = outputbasedir+ext+'/'+time.strftime('%Y-%m/%d/%H/', curtime)
    # if the folder doesn't exist make it
    if not os.path.exists(name):
        os.makedirs(name)
    return name

def output_mode():
    global videorecording, audiorecording, tl_count, loadlimitbreached, videosizelimitreached, audiosizelimitreached, sizewarningreached, transferring

    # Mode lights
    # Status - Off = Not running
    # Status -Red = Disk space too low, audio & video will not record

    if audiosizelimitreached:
        if (debug):
            print("audiosizelimitreached Red =", audiosizelimitreached)
        GPIO.output( statusLED_R, False)
        GPIO.output( statusLED_G, True)
        GPIO.output( statusLED_B, True)
        
    elif videorecording:
        #print("videorecording blue?=", videorecording)
        # Status -Blue = Video recording
        GPIO.output( statusLED_R, True)
        GPIO.output( statusLED_G, True)
        GPIO.output( statusLED_B, False)
        
    elif audiorecording:
        #print("audiorecording cyan?=", audiorecording)
        # Status -cyan = Audio recording
        GPIO.output( statusLED_R, True)
        GPIO.output( statusLED_G, False)
        GPIO.output( statusLED_B, False)
        
    else:
        # Status -green = Timelapse mode
        #print("timelapse should be green")
        GPIO.output( statusLED_R, True)
        GPIO.output( statusLED_G, False)
        GPIO.output( statusLED_B, True)
    

def output_status():
    global videorecording, audiorecording, tl_count, loadlimitbreached, videosizelimitreached, audiosizelimitreached, sizewarningreached, transferring
    
    
    if (tl_count % 20) == 0:
        if (False and debug):
        
            print("videorecording blue?=", videorecording)
            print("audiorecording cyan?=", audiorecording)
        
            print("Output status:-")
            print("transferring =", transferring)
            print("videosizelimitreached =", videosizelimitreached)
            print("audiosizelimitreached =", audiosizelimitreached)
            print("sizewarningreached =", sizewarningreached)
            print("loadlimitbreached =", loadlimitbreached)
        
    if (tl_count % 2):        
        if transferring:
            # Status -Flashing white = Transferring
            GPIO.output( statusLED_R, False)
            GPIO.output( statusLED_G, False)
            GPIO.output( statusLED_B, False)
        
        elif videosizelimitreached:
            # Status -Flashing Yellow = Disk space getting low
            GPIO.output( statusLED_R, False)
            GPIO.output( statusLED_G, True)
            GPIO.output( statusLED_B, True)
            
        elif sizewarningreached:
            # Status -Flashing Red = Disk space too low, video will not record
            GPIO.output( statusLED_R, False)
            GPIO.output( statusLED_G, False)
            GPIO.output( statusLED_B, True)
            
        
        elif loadlimitbreached:
            # Status -Flashing Magenta = CPU too stressed
            GPIO.output( statusLED_R, False)
            GPIO.output( statusLED_G, True)
            GPIO.output( statusLED_B, False)
            
        else:
            output_mode()
    else:
            output_mode()
    
        
# Take a timelapse shot    
def dotimelapse():
    if not audiosizelimitreached:
        
        
        camera.exif_tags['EXIF.Copyright'] = 'Copyright (c) 2014 the Long Well Walk'
        
        if not (math.isnan(gpsc.fix.latitude) or math.isnan(gpsc.fix.longitude)) and gpsc.fix.latitude and gpsc.fix.longitude:
            if (debug):
                print "latitude ", gpsc.fix.latitude
                print "longitude ", gpsc.fix.longitude
                print "altitude (m)", gpsc.fix.altitude
            
            
            # TODO :  Test that the GPS data set in EXIF properl;y fits the spec and is readable
            # Spec here http://www.digicamsoft.com/exif22/exif22/html/exif22_53.htm
            
            camera.exif_tags['GPS.GPSVersionID'] = "2.2.0.0"
    
            if gpsc.fix.latitude >= 0:
                camera.exif_tags['GPS.GPSLatitudeRef'] = "N"
            else:
                camera.exif_tags['GPS.GPSLatitudeRef'] = "S"
            
            #dd/1,mmmm/100,0/1
            lat = math.fabs(gpsc.fix.latitude)
            deg = math.floor(lat)
            # TODO : Change to deg/1 min/1 sec/1 integer format
            degmin = math.floor(10000 * (lat - deg))
            camera.exif_tags['GPS.GPSLatitude'] = '{},{},00'.format(deg, degmin)
            
    
            if gpsc.fix.longitude >= 0:
                camera.exif_tags['GPS.GPSLongitudeRef'] = "E"
            else:
                camera.exif_tags['GPS.GPSLongitudeRef'] = "W"
            
            #dd/1,mmmm/100,0/1
            longitude = math.fabs(gpsc.fix.longitude)
            deg = math.floor(longitude)
            # TODO : Change to deg/1 min/1 sec/1 integer format
            degmin = math.floor(10000 * (longitude - deg))
            camera.exif_tags['GPS.GPSLongitude'] = '{},{},00'.format(deg, degmin)
            
    
            if gpsc.fix.altitude >= 0:
                camera.exif_tags['GPS.GPSAltitudeRef'] = "0"
            else:
                camera.exif_tags['GPS.GPSAltitudeRef'] = "1"
            
            camera.exif_tags['GPS.GPSAltitude'] ='{}'.format(math.fabs(gpsc.fix.altitude))
            
            gpslogline = '{},{},{},{}'.format(time.time(), gpsc.fix.latitude, gpsc.fix.longitude, gpsc.fix.altitude)
            
            # TODO : Write the gpslogline to a GPS file.
            #file.write(gpslogline)
            
            if (debug):
                print("time.time =", time.time())
                print("gpslogline =", gpslogline)


        #GPSTimeStamp, GPSSatellites, GPSStatus, GPSMeasureMode, GPSDOP, GPSSpeedRef, GPSSpeed, GPSTrackRef, GPSTrack, GPSImgDirectionRef, GPSImgDirection, GPSMapDatum, GPSDestLatitudeRef, GPSDestLatitude, GPSDestLongitudeRef, GPSDestLongitude, GPSDestBearingRef, GPSDestBearing, GPSDestDistanceRef, GPSDestDistance, GPSProcessingMethod, GPSAreaInformation, GPSDateStamp, GPSDifferential
        
        stillnow = time.gmtime()
        stillname = getFolderName(stillnow,'jpg')+getFileName(stillnow,'jpg')
        
        camera.capture(stillname, use_video_port=True)
        if (debug):
            print("still "+stillname)
    
    
def write_video(stream):
    # Write the entire content of the circular buffer to disk. No need to
    # lock the stream here as we're definitely not writing to it
    # simultaneously
    then = time.gmtime(time.time() - buffer_length)
    videoname = getFolderName(then,'h264')+getFileName(then,'h264')
        
    if (debug):
        print("buffer video writing "+videoname)

    with io.open(videoname, 'wb') as output:
        for frame in stream.frames:
            if frame.header:
                stream.seek(frame.position)
                break
        while True:
            buf = stream.read1()
            if not buf:
                break
            output.write(buf)
    # Wipe the circular stream once we're done
    stream.seek(0)
    stream.truncate()
    if (debug):
        print("buffer video ending "+videoname)

def checkstatus():
    global videorecording, audiorecording, tl_count, loadlimitbreached, videosizelimitreached, audiosizelimitreached, sizewarningreached, transferring
    # Have we run out of disk space
    stats = os.statvfs(outputbasedir)
    
    videosizelimitreached = stats.f_bfree < videosizelimit
    
    audiosizelimitreached = stats.f_bfree < audiosizelimit
    sizewarningreached    = stats.f_bfree < sizewarning
        
    loadavg, loadavg5, loadavg15 = os.getloadavg()
    loadlimitbreached = loadavg>loadavglimit
    
    if (debug):
        print("Checkstatus:-","stats.f_bfree =", stats.f_bfree,"videosizelimitreached =", videosizelimitreached, "audiosizelimitreached =", audiosizelimitreached, "sizewarningreached =", sizewarningreached,"loadavg =", loadavg, "loadlimitbreached =", loadlimitbreached)
    

#Main Code Starts here

#create GPS controller
gpsc = GpsController()

#start controller
gpsc.start()

# GPIO setup
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD) # Use the standard RPi pin numbers
GPIO.setup(videobutton,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   # Set as Input which is usually off
GPIO.setup(audiobutton, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    # Set as Input which is usually off

if not poweroffbutton == audiobutton: 
    GPIO.setup(poweroffbutton, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    # Set as Input which is usually off

GPIO.setup(statusLED_R, GPIO.OUT)   # Set as Output
GPIO.setup(statusLED_G, GPIO.OUT)   # Set as Output
GPIO.setup(statusLED_B, GPIO.OUT)   # Set as Output

if (debug):
    print("backback started")

with picamera.PiCamera() as camera:
    # Start up the Camera
    camera.resolution = (1920, 1080)   #1080P Full HD 1920x1080
    #camera.resolution = (1280, 720)     #720P HD 1280x720
    camera.framerate = 25
    stream = picamera.PiCameraCircularIO(camera, seconds=buffer_length)
    camera.start_recording(stream, format='h264')    
    
    duration_step = 1
    duration_timelapse = 60
    duration_first_timelapse = 5
    
    
    current_time = time.clock()
    next_step = current_time + duration_step
    next_timelapse = current_time + duration_first_timelapse

    
    # Have we run out of disk space            
    checkstatus()
    output_status()
    
    GPIO.add_event_detect(videobutton, GPIO.BOTH)  # Start listening out for button presses
    GPIO.add_event_detect(audiobutton, GPIO.BOTH)  # Start listening out for button presses
    if not poweroffbutton == audiobutton: 
        GPIO.add_event_detect(poweroffbutton, GPIO.BOTH)  # Start listening out for button presses
       
    try:
        while True:
            camera.wait_recording(cycle_wait)    # Pause in loop
            current_time =  time.clock()
                        
            #visual stuff
            if(current_time >= next_step):
                next_step = current_time + duration_step
                
                # check GPS time and if it ahead of RPi time update RPi time
                if gpsc.utc and gpsc.utc<>"None":
                    print "time utc ", gpsc.utc #, " + ", gpsc.fix.time
                    
                    sattime = time.mktime(time.strptime(gpsc.utc, "%Y-%m-%dT%H:%M:%S.000Z"))
                    print("sattime =", sattime)
                    print("time.time =", time.time())
                    if (time.time() < sattime):
                        print "setting time"
                        os.system('date -s %s' % gpsc.utc)
                
                    print gpsc.fix
            
                if(current_time >= next_timelapse):                
                    dotimelapse()
                    next_timelapse = current_time + duration_timelapse
                    # Have we run out of disk space
                    checkstatus()
                
                couldbeaudio = False
                if GPIO.event_detected(poweroffbutton):
                    if audiobutton == poweroffbutton: 
                        couldbeaudio = True
                    powerclickcount = powerclickcount + poweroffclickstep
                    if (debug):
                        print("powerclickcount =", powerclickcount)
                
                elif powerclickcount > 0:
                    powerclickcount = powerclickcount - 1
    
                if powerclickcount >= poweroffclicktarget:
                    if (debug):
                        print ("Power off triggered stopping")
                    
                    GPIO.output( statusLED_R, False) 
                    GPIO.output( statusLED_G, True)
                    GPIO.output( statusLED_B, True)


                    camera.split_recording(stream)
                    videorecording = False
                            
                    os.system("sudo shutdown -F -h -t 30 now") #not sure about the -F which forces fsck on next boot
                    sys.exit()
    
                # Have we run out whilst recording video
                if audiosizelimitreached and audiorecording:
                    # TODO : Stop recording
                    audiorecording = False
                    subprocess.call("killall arecord", shell=True)
                                
                    
                    if (debug):
                        print ("limit breached audio stopping")
                
                
                if GPIO.event_detected(audiobutton) or couldbeaudio:
                    # TODO :34 Audio
                    # this is the audio blog button
                    if (debug):
                        print('Audio Button Pressed!')
                        
                        if audiorecording:
                            if (not videorecording) or audiosizelimitreached:
                                audiorecording = False
                                subprocess.call("killall arecord", shell=True)
                                
                                if (debug):
                                    print ("ending recording")
                
                        else:
                            now = time.gmtime()
                            audiofilename = getFolderName(now,'wav')+getFileName(now,'wav')
                            AudioRecordingProcess = subprocess.Popen(arecordcmd+audiofilename, shell=True)
                            audiorecording = True
                            
                            if (debug):
                                print ("recordinging into ", audiofilename)
                        
                            
                            
                # Have we run out whilst recording video
                if videosizelimitreached and videorecording:
                    camera.split_recording(stream)
                    
                    videorecording = False
                    if (debug):
                        print ("limit breached video stopping")
                
                
                # Has the video button been pressed?
                if GPIO.event_detected(videobutton) and not videosizelimitreached:
                    if (debug):
                        print('Video Button Clicked!')
                    
                    # If we are recording stop recording
                    if videorecording:
                        if (debug):
                            print('Button pressed to stop ')
                        # Go back to recording to the ring buffer not the file
                        camera.split_recording(stream)
                        videorecording = False
                        audiorecording = False
                        subprocess.call("killall arecord", shell=True)
                                
                        
                        if (debug):
                            print("button video ending "+videoname)
                    else:
                        videorecording = True
                        output_mode()
                        # What should the video be called
                        now = time.gmtime()
                        videoname = getFolderName(now,'h264')+getFileName(now,'h264')

                        audiofilename = getFolderName(now,'wav')+getFileName(now,'wav')
                        
                        # TODO : Start recording audio
                        AudioRecordingProcess = subprocess.Popen(arecordcmd+audiofilename, shell=True)
                        
                        
                        if (debug):
                            print("button video starting "+videoname)
                        
                        # Send video to the file
                        camera.split_recording(videoname)
                        
                        # TODO : #34 Audio Recording
                        # TODO : the video triggers the wide angle audio
                        # TODO : workout if we can have an audio ring buffer
                        
                        
                        # Save the ring buffer to the disk
                        write_video(stream)
                
                # Set the output lights
                output_status()

    finally:
        # Tidy up when the program stops
        camera.stop_recording()
        if (debug):
            print("stopping ending ")
        GPIO.output( statusLED_R, True) 
        GPIO.output( statusLED_G, True)
        GPIO.output( statusLED_B, True)
        GPIO.cleanup()
        #stop GPS controller
        gpsc.stopController()
        gpsc.join()

