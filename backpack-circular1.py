import picamera
import time
import os
import io
import random
import picamera
import RPi.GPIO as GPIO 

tl_count = 60
tl_target = 60
startuppause = 5
buffer_length = 15

videobutton = 11
audiobutton = 12

statusLED_R = 10
statusLED_G = 10
statusLED_B = 10



GPIO.setmode(GPIO.BOARD)

GPIO.cleanup()

GPIO.setup(videobutton,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(audiobutton, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(statusLED_R, GPIO.OUT)


#outputbasedir =  os.path.expanduser('~/BPOA/') 

outputbasedir =  os.path.expanduser('/home/pi/BPOA/')
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
    # TODO : Add checking status and setting LED's
    GPIO.output( statusLED_R, True) 
    if (debug):
        print("output ")


def check_buttons():
    result = GPIO.input(videobutton)
    
    # TODO : Add seperate audio testing
    #if (debug):
    #    print("result ")
    #    print(result)
    return result

def dotimelapse():
    global tl_count, tl_target
    # TODO : Move to time based check (this drifts by about 0.5% per cycle)
    tl_count = tl_count + 1
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

time.sleep(5)

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
                write_video(stream)
                
                while check_buttons():
                    camera.wait_recording(1)
                    dotimelapse()
                print('Button unpressed')
                camera.split_recording(stream)
                if (debug):
                    print("button video ending "+videoname)


            output_status()

    finally:
        camera.stop_recording()
        if (debug):
            print("stopping ending ")
        GPIO.cleanup()

