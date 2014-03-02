# Raspberry Pi based system for recording and transmitting data from a lone long distance walker.
# Being built for http://thelongwellwalk.org/

#Import the supporting code we need
import picamera         # Controlling the Camera
import time             # Time and Date functions
import os               # Operating system information and functions
import io               # Input and Output (Files and streams))
import RPi.GPIO as GPIO # Controls the GPIO for LEDs and Buttons

#Config
tl_target = 60          # How long between each Timelapse shot
buffer_length = 15      # How many seconds worth of video do we keep in the buffer
debug = True            # Do we print out debugging messages
f_favail_limit = 20000  # How much disk space is too little space (measured in blocks)

#Where are files stored
outputbasedir =  os.path.expanduser('/home/pi/BPOA/')

#GPIO Config
# Which GPIO pin does what job?
videobutton = 11        # Video (currently rigged as momentary switch) 
audiobutton = 12        # Audio (no code so far)

statusLED_R = 10        # Red LED, short wire on own
statusLED_G = 7         # Green LED middle length wire
statusLED_B = 8         # Blue LED short wire next to middle length
#The GND wire is the longest and is wired through a switch so it only shows when pressed


# Status variables
videorecording = False  # Are we currently recording video
audiorecording = False  # Are we currently recording audio
tl_count  = 55          # Starting Timelapse count 55 means it will take 5 seconds to do first timlapse

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

# Change the output LEDs to show Liam what is going on
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
    
# Take a timelapse shot    
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



#Main Code Starts here

# GPIO setup
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD) # Use the standard RPi pin numbers
GPIO.setup(videobutton,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   # Set as Input which is usually off
GPIO.setup(audiobutton, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    # Set as Input which is usually off
GPIO.setup(statusLED_R, GPIO.OUT)   # Set as Output
GPIO.setup(statusLED_G, GPIO.OUT)   # Set as Output
GPIO.setup(statusLED_B, GPIO.OUT)   # Set as Output

if (debug):
    print("backback started")

with picamera.PiCamera() as camera:
    # Start up the Camera
    #camera.resolution = (1920, 1080)   #1080P Full HD 1920x1080
    camera.resolution = (1280, 720)     #720P HD 1280x720
    camera.framerate = 25
    stream = picamera.PiCameraCircularIO(camera, seconds=buffer_length)
    camera.start_recording(stream, format='h264')
    
    
    GPIO.add_event_detect(videobutton, GPIO.RISING)  # Start listening out for button presses
    GPIO.add_event_detect(audiobutton, GPIO.RISING)  # Start listening out for audio button presses
    
    # Have we run out of disk space
    stats = os.statvfs(outputbasedir)
    sizelimitreached = stats.f_bfree < f_favail_limit
                
    try:
        while True:
            camera.wait_recording(1)    # Pause in loop
            
            # Is it time to take a timelapse shot
            tl_count = tl_count + 1
            if (tl_count >= tl_target):
                tl_count = 0
                dotimelapse()
                # Have we run out of disk space
                stats = os.statvfs(outputbasedir)
                sizelimitreached = stats.f_bfree < f_favail_limit
            
            # Have we run out whilst recording video
            if sizelimitreached and videorecording:
                camera.split_recording(stream)
                videorecording = False
                if (debug):
                    print ("limit breached video stopping")
            
            if GPIO.event_detected(audiobutton) and not sizelimitreached:
                # TODO :34 Audio
                # this is the audio blog button
                if (debug):
                    print('Audio Button Pressed!')
                    
                        
            
            # Has the video button been pressed?
            if GPIO.event_detected(videobutton) and not sizelimitreached:
                if (debug):
                    print('Video Button Pressed!')
                
                # If we are recording stop recording
                if videorecording:
                    if (debug):
                        print('Button pressed to stop ')
                    # Go back to recording to the ring buffer not the file
                    camera.split_recording(stream)
                    videorecording = False
                    if (debug):
                        print("button video ending "+videoname)
                else:
                    # What should the video be called
                    now = time.gmtime()
                    videoname = getFolderName(now,'h264')+getFileName(now,'h264')
                    videorecording = True
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
        GPIO.output( statusLED_R, False) 
        GPIO.output( statusLED_G, False)
        GPIO.output( statusLED_B, False)
        GPIO.cleanup()

