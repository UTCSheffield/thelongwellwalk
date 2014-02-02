import picamera
import time
import os
import io
import random
import picamera
from PIL import Image
import RPi.GPIO as GPIO 


prior_image = None
tl_count = 0
tl_target = 60
startuppause = 5
buffer_length = 15

videobutton = 8
statusbutton = 9

statusLED = 10

GPIO.setup(videobutton,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(statusbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(statusLED, GPIO.OUT)


outputbasedir =  os.path.expanduser('~/BPOA/') 
videocachedir = outputbasedir+'videocache/'

timelapsedir = os.path.expanduser('~/timelapse')
debug = True


def getFileName(curtime, ext):
    name = time.strftime("%Y-%m-%d-%H-%M-%S", curtime)+"."+ext
    return name
  
def getFolderName(curtime, ext):
    name = outputbasedir+ext+'/'+time.strftime('%Y-%m/%d/%H/', curtime)+'/'
    if( os.path.exists(name) != True ):
        os.makedirs(name)
    return name

def output_status():
    #not checking anything at the mo
    GPIO.output( statusLED, True) 

def check_buttons():
    if (GPIO.input(statusbutton)):
        output_status()
    else:
        GPIO.output( statusLED, False)
    result = GPIO.input(videobutton)
    return result

def dotimelapse():
    global tl_count, tl_target
    tl_count ++
    if (tl_count >= tl_target):
        tl_count = 0
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


if (debug):
    print("backback started")

if( os.path.exists(videocachedir) != True ):
    os.makedirs(videocachedir)

with picamera.PiCamera() as camera:
    camera.resolution = (1920, 1080) #1080P Full HD 1920x1080
    camera.framerate = 25
    stream = picamera.PiCameraCircularIO(camera, seconds=buffer_length)
    camera.start_recording(stream, format='h264')
    try:
        while True:
            camera.wait_recording(1)
            dotimelapse()
            if check_buttons():
                print('Button Pressed!')
                
                now = time.gmtime()
                videoname = getFolderName(now,'h264')+getFileName(now,'h264')
                if (debug):
                    print("button video starting "+videoname)

                camera.split_recording(videoname)
                # Write the buffer before the button press to disk as well
                write_video(stream)
                # Wait until motion is no longer detected, then split
                # recording back to the in-memory circular buffer
                while check_buttons():
                    camera.wait_recording(1)
                    dotimelapse()
                print('Button unpressed')
                camera.split_recording(stream)
                if (debug):
                    print("button video ending "+videoname)

    finally:
        camera.stop_recording()
