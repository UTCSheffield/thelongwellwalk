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
import re
                    

#Config
buffer_length = 15      # How many seconds worth of video do we keep in the buffer
debug = True            # Do we print out debugging messages
f_favail_limit = 20000  # How much disk space is too little space (measured in blocks)

arecordcmd = "arecord -D plughw:1,0 "
# TODO : use the --max-file-time on the audio files


duration_step = 1
#duration_timelapse = 60
duration_timelapse = 20
duration_first_timelapse = 5

next_step = 0
next_timelapse = 0

cycle_wait = 0.5

poweroffclicktarget = 6
poweroffclickstep = 2
powerclickcount = 0

videosizelimit = 20000
audiosizelimit = 10000
jpgsizelimit = 10000
sizewarning    = 50000

loadavglimit = 1.25

#Where are files stored
outputbasedir =  os.path.expanduser('/home/pi/BPOA/')

#GPIO Config
# Which GPIO pin does what job
videobutton = 11        # Video (currently rigged as momentary switch) 
audiobutton = 12        # Audio (no code so far)
poweroffbutton = 12        # Poweroff button (can be same as audio)

statusLED_R = 15 #10 # Red LED, short wire on own
statusLED_G = 18 # 7 # Green LED middle length wire
statusLED_B = 16 # 8 # Blue LED short wire next to middle length


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
jpgsizelimitreached = False
transferring = False

lastutc = ""


# Functions

# Work out the file name based on the current time and file type
def getFileName(curtime, ext):
    if ext == "gps":
        name = time.strftime("%Y-%m-%d-%H", curtime)+"."+ext
    else:    
        name = time.strftime("%Y-%m-%d-%H-%M-%S", curtime)+"."+ext
    return name

# Work out the file folder based on the current time and file type
def getFolderName(curtime, ext):
    if ext == "gps":
        name = outputbasedir+ext+'/'+time.strftime("%Y-%m/%d/", curtime)
    else:    
        name = outputbasedir+ext+'/'+time.strftime('%Y-%m/%d/%H/', curtime)
    # if the folder doesn't exist make it
    if not os.path.exists(name):
        os.makedirs(name)
    return name

def output_mode():
    global jpgsizelimitreached, videorecording, audiorecording, tl_count, loadlimitbreached, videosizelimitreached, audiosizelimitreached, sizewarningreached, transferring

    # Mode lights
    if jpgsizelimitreached:
        if (debug):
            print("jpgsizelimitreached Red =", audiosizelimitreached)
        GPIO.output( statusLED_R, False)
        GPIO.output( statusLED_G, True)
        GPIO.output( statusLED_B, True)
        
    elif videorecording:
        # Status -Blue = Video recording
        GPIO.output( statusLED_R, True)
        GPIO.output( statusLED_G, True)
        GPIO.output( statusLED_B, False)
        
    elif audiorecording:
        # Status -cyan = Audio recording
        GPIO.output( statusLED_R, True)
        GPIO.output( statusLED_G, False)
        GPIO.output( statusLED_B, False)
        
    else:
        # Status -green = Timelapse mode
        GPIO.output( statusLED_R, True)
        GPIO.output( statusLED_G, False)
        GPIO.output( statusLED_B, True)
    

def output_status():
    global jpgsizelimitreached, videorecording, audiorecording, tl_count, loadlimitbreached, videosizelimitreached, audiosizelimitreached, sizewarningreached, transferring
    
    
    if (math.floor(current_time) % 20) == 0:  
        if (debug):
            if videorecording:
                print("videorecording blue?=", videorecording)
            if audiorecording:
                print("audiorecording cyan?=", audiorecording)
            if transferring:
                print("transferring =", transferring)
            if videosizelimitreached:
                print("videosizelimitreached =", videosizelimitreached)
            if audiosizelimitreached:
                print("audiosizelimitreached =", audiosizelimitreached)
            if sizewarningreached:
                print("sizewarningreached =", sizewarningreached)
            if loadlimitbreached:
                print("loadlimitbreached =", loadlimitbreached)
        
    if math.floor(current_time) % 2:          
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
    
def splitDegrees(fDeg):
    iDeg = math.floor(fDeg)
    fMin = 60 * (fDeg - iDeg)
    iMin = math.floor(fMin)
    fSecs = 60 * (fMin - iMin)
    iSecs = math.floor(fSecs)
    return [iDeg, iMin, iSecs]
            
# Take a timelapse shot    
def dotimelapse():
    if not jpgsizelimitreached:
        camera.exif_tags['EXIF.Copyright'] = 'Copyright (c) 2014 the Long Well Walk'
        
        if not (math.isnan(gpsc.fix.latitude) or math.isnan(gpsc.fix.longitude)) and gpsc.fix.latitude and gpsc.fix.longitude:
            if (debug):
                print "latitude ", gpsc.fix.latitude
                print "longitude ", gpsc.fix.longitude
                print "altitude (m)", gpsc.fix.altitude
            
            # DONE :  Test that the GPS data set in EXIF properly fits the spec and is readable
            # Spec here http://www.digicamsoft.com/exif22/exif22/html/exif22_53.htm
            
            camera.exif_tags['GPS.GPSVersionID'] = "2.2.0.0"
    
            if gpsc.fix.latitude >= 0:
                camera.exif_tags['GPS.GPSLatitudeRef'] = "N"
            else:
                camera.exif_tags['GPS.GPSLatitudeRef'] = "S"
            
            lat = math.fabs(gpsc.fix.latitude)
            iDeg, iMin, iSecs = splitDegrees(lat)
            #dd/1,mm/1,ss/1
            camera.exif_tags['GPS.GPSLatitude'] = '{},{},{}'.format(iDeg+0.1, iMin+0.1, iSecs+0.1)
            
            if gpsc.fix.longitude >= 0:
                camera.exif_tags['GPS.GPSLongitudeRef'] = "E"
            else:
                camera.exif_tags['GPS.GPSLongitudeRef'] = "W"
            
            
            longitude = math.fabs(gpsc.fix.longitude)
            iDeg, iMin, iSecs = splitDegrees(longitude)
            #dd/1,mm/1,ss/1
            camera.exif_tags['GPS.GPSLongitude'] = '{},{},{}'.format(iDeg+0.1, iMin+0.1, iSecs+0.1)
            
    
            if gpsc.fix.altitude >= 0:
                camera.exif_tags['GPS.GPSAltitudeRef'] = "0"
            else:
                camera.exif_tags['GPS.GPSAltitudeRef'] = "1"
            
            camera.exif_tags['GPS.GPSAltitude'] ='{}'.format(math.fabs(gpsc.fix.altitude))
            
            gpslogline = '{},{},{},{},{}\n'.format(math.floor(time.time()), gpsc.utc, gpsc.fix.latitude, gpsc.fix.longitude, gpsc.fix.altitude)
            
            # TODO : Write the gpslogline to a GPS file.
            gpsnow = time.gmtime()
            gpsname = getFolderName(gpsnow,'gps')+getFileName(gpsnow,'gps')
            print("gpsname =", gpsname)
            
            with open(gpsname, "a") as gpsfile:
                gpsfile.write(gpslogline)
            
            if (debug):
                print("gpslogline =", gpslogline)


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
    global jpgsizelimitreached, videorecording, audiorecording, tl_count, loadlimitbreached, videosizelimitreached, audiosizelimitreached, sizewarningreached, transferring
    # Have we run out of disk space
    
    now = time.gmtime()
    
    videofolder = getFolderName(now,'h264')
    stats = os.statvfs(videofolder)
    videosizelimitreached = stats.f_bfree < videosizelimit
    if (debug):
        print("video.f_bfree =", stats.f_bfree)
    
    audiofolder = getFolderName(now,'wav')
    stats = os.statvfs(audiofolder)
    audiosizelimitreached = stats.f_bfree < audiosizelimit
    if (debug):
        print("audio.f_bfree =", stats.f_bfree)
    sizewarningreached    = stats.f_bfree < sizewarning
        
    
    jpgfolder = getFolderName(now,'jpg')
    stats = os.statvfs(jpgfolder)
    jpgsizelimitreached = stats.f_bfree < jpgsizelimit
    if (debug):
        print("jpg.f_bfree =", stats.f_bfree)
    sizewarningreached    = sizewarningreached or (stats.f_bfree < sizewarning)
    
        
    loadavg, loadavg5, loadavg15 = os.getloadavg()
    loadlimitbreached = loadavg>loadavglimit
    
    if (debug):
        print("Checkstatus:-","stats.f_bfree =", stats.f_bfree,"jpgsizelimitreached",jpgsizelimitreached, "videosizelimitreached =", videosizelimitreached, "audiosizelimitreached =", audiosizelimitreached, "sizewarningreached =", sizewarningreached,"loadavg =", loadavg, "loadlimitbreached =", loadlimitbreached)

    

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
    
    
    
    
    current_time = time.time()
    print("current_time =", current_time)
    next_step = current_time + duration_step
    next_timelapse = current_time + duration_first_timelapse

    
    # Have we run out of disk space            
    checkstatus()
    output_status()
    
    GPIO.add_event_detect(videobutton, GPIO.BOTH, bouncetime=300)  # Start listening out for button presses
    GPIO.add_event_detect(audiobutton, GPIO.BOTH, bouncetime=300)  # Start listening out for button presses
    if not poweroffbutton == audiobutton: 
        GPIO.add_event_detect(poweroffbutton, GPIO.BOTH, bouncetime=300)  # Start listening out for button presses
    
    lastvideobuttonstate = GPIO.input(videobutton)
    lastaudiobuttonstate = GPIO.input(audiobutton)
    lastpoweroffbuttonstate = GPIO.input(poweroffbutton)
    
    try:
        while True:
            camera.wait_recording(cycle_wait)    # Pause in loop
            
            videobuttonpressednow = False
            if GPIO.event_detected(videobutton):
                videobuttonpressednow = (GPIO.input(videobutton) <> lastvideobuttonstate)
                lastvideobuttonstate = GPIO.input(videobutton)
            
            poweroffbuttonpressednow = False
            couldbeaudio = False
            if GPIO.event_detected(poweroffbutton):
                poweroffbuttonpressednow = (GPIO.input(poweroffbutton) <> lastpoweroffbuttonstate)
                lastpoweroffbuttonstate = GPIO.input(poweroffbutton)
                if poweroffbuttonpressednow and audiobutton == poweroffbutton: 
                    couldbeaudio = True
            
            audiobuttonpressednow = False
            if GPIO.event_detected(audiobutton):
                print("audiobutton =", audiobutton)
                audiobuttonpressednow = (GPIO.input(audiobutton) <> lastaudiobuttonstate)
                lastaudiobuttonstate = GPIO.input(audiobutton)
                print("audiobuttonpressednow =", audiobuttonpressednow)
            
        
        
            current_time =  time.time()
            #print("current_time =", current_time)
                        
            #visual stuff
            if(current_time >= next_step):
                #next_step = current_time + duration_step
                next_step = next_step + duration_step
                #print("next_step =", next_step)
                
                # check GPS time and if it ahead of RPi time update RPi time
                if not (math.isnan(gpsc.fix.latitude) or math.isnan(gpsc.fix.longitude)) and gpsc.fix.latitude and gpsc.fix.longitude and gpsc.utc and gpsc.utc<>"None":
                    if gpsc.utc <> lastutc:
                        lastutc = gpsc.utc
                        timetoseconds = re.sub(r'\.[0-9][0-9][0-9]Z', r'Z', lastutc)
                        sattime = time.mktime(time.strptime(timetoseconds, "%Y-%m-%dT%H:%M:%SZ"))
                        if debug:
                            print("sattime    =", sattime)
                            print("time.time =", time.time())
                        if (time.time() < sattime):
                            print "setting time"
                            os.system('date -s %s' % lastutc)
                
            if(current_time >= next_timelapse):                
                dotimelapse()
                next_timelapse = next_timelapse + duration_timelapse
                # Have we run out of disk space
                checkstatus()
            
            
            #Fast reacting stuff    
            if poweroffbuttonpressednow:
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
                        
                os.system("sudo shutdown -h -t 30 now") #not sure about the -F which forces fsck on next boot
                sys.exit()

            # Have we run out whilst recording video
            if audiosizelimitreached and audiorecording:
                # TODO : Stop recording
                audiorecording = False
                subprocess.call("killall arecord", shell=True)
                            
                
                if (debug):
                    print ("limit breached audio stopping")
            
            
            if audiobuttonpressednow or couldbeaudio:
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
            if videobuttonpressednow and not videosizelimitreached:
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

