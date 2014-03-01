import picamera
import time
import os
import io
import random
import picamera
import RPi.GPIO as GPIO 

tl_count = 56
tl_target = 60
startuppause = 5
buffer_length = 15

videobutton = 11
audiobutton = 12

videorecording = False
audiorecording = False

f_favail_limit = 20000
#f_favail_limit = 2000000000

statusLED_R = 10  # short on own
statusLED_G = 7  # mid
statusLED_B = 8  #short
#the GND the longest

min_video_length = 15 # seconds

outputbasedir =  os.path.expanduser('/home/pi/BPOA/')
debug = True

GPIO.cleanup()


GPIO.setmode(GPIO.BOARD)

GPIO.setup(videobutton,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(audiobutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(statusLED_R, GPIO.OUT)
GPIO.setup(statusLED_G, GPIO.OUT)
GPIO.setup(statusLED_B, GPIO.OUT)


def getFileName(curtime, ext):
    name = time.strftime("%Y-%m-%d-%H-%M-%S", curtime)+"."+ext
    return name
  
def getFolderName(curtime, ext):
    name = outputbasedir+ext+'/'+time.strftime('%Y-%m/%d/%H/', curtime)
    if not os.path.exists(name):
        os.makedirs(name)
    return name

def output_status():
    global videorecording, sizelimitreached, tl_count
    #not checking anything at the mo
    # TODO : Add checking status and setting LED's
    if sizelimitreached:
        GPIO.output( statusLED_R, True)
    else:    
        GPIO.output( statusLED_G, True)
        if videorecording:
            GPIO.output( statusLED_R, (tl_count % 2)) #flashing green / yellow for recording
    #GPIO.output( statusLED_R, videorecording)
    
    # blue wire is broken just at the moment 
    #GPIO.output( statusLED_B, videorecording) 
    
    
def dotimelapse():
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



#Main
if (debug):
    print("backback started")

with picamera.PiCamera() as camera:
    #camera.resolution = (1920, 1080) #1080P Full HD 1920x1080
    camera.resolution = (1280, 720) #720P HD 1280x720
    
    camera.framerate = 25
    stream = picamera.PiCameraCircularIO(camera, seconds=buffer_length)
    camera.start_recording(stream, format='h264')
    
    GPIO.add_event_detect(videobutton, GPIO.RISING)  # add rising edge detection on a channel
    
    stats = os.statvfs(outputbasedir)
    sizelimitreached = stats.f_bfree < f_favail_limit
                
    try:
        while True:
            camera.wait_recording(1)
            tl_count = tl_count + 1
            if (tl_count >= tl_target):
                tl_count = 0
                dotimelapse()
                stats = os.statvfs(outputbasedir)
                sizelimitreached = stats.f_bfree < f_favail_limit
            
            if sizelimitreached and videorecording:
                camera.split_recording(stream)
                videorecording = False
                if (debug):
                    print ("limit breached video stopping")
                        
            
            
            if GPIO.event_detected(videobutton) and not sizelimitreached:
                if (debug):
                    print('Video Button Pressed!')
                
                if videorecording:                
                    if (debug):
                        print('Button pressed to stop ')
                    camera.split_recording(stream)
                    videorecording = False
                    if (debug):
                        print("button video ending "+videoname)
                else:
                    now = time.gmtime()
                    videoname = getFolderName(now,'h264')+getFileName(now,'h264')
                    videorecording = True
                    if (debug):
                        print("button video starting "+videoname)
    
                    camera.split_recording(videoname)
                    write_video(stream)
        
            output_status()

    finally:
        camera.stop_recording()
        if (debug):
            print("stopping ending ")
        GPIO.output( statusLED_R, False) 
        GPIO.output( statusLED_G, False)
        GPIO.output( statusLED_B, False)
        GPIO.cleanup()

