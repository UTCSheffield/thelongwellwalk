import picamera
import time
import os


outputbasedir =  os.path.expanduser('~/BPOA/') 
videocachedir = outputbasedir+'videocache/'

startuppause = 5
timelapsedir = os.path.expanduser('~/timelapse')
debug = True

if (debug):
  print("backback started")

def getFileName(curtime, ext):
  name = time.strftime("%Y-%m-%d-%H-%M-%S", curtime)+"."+ext
  return name
  
def getFolderName(curtime, ext):
  name = outputbasedir+ext+'/'+time.strftime('%Y-%m/%d/%H/', curtime)+'/'
  if( os.path.exists(name) != True ):
    os.makedirs(name)
  return name

if( os.path.exists(videocachedir) != True ):
  os.makedirs(videocachedir)

with picamera.PiCamera() as camera:
  

  #Power up
  #camera.resolution = (1920, 1080) #1080P Full HD 1920x1080
  camera.resolution = (1280, 720)
  camera.framerate = 25
  
  #camera.start_preview()
  time.sleep(startuppause)
  start = time.gmtime()

  
  #calc name
  videoname = videocachedir+getFileName(start,'h264')
  camera.start_recording(videoname,  inline_headers=True)
  if (debug):
    print("video started "+videoname)

  
  while True:
    camera.wait_recording(10)
    stillnow = time.gmtime()
    stillname = getFolderName(stillnow,'jpg')+getFileName(stillnow,'jpg')
    
    camera.capture(stillname, use_video_port=True)
    if (debug):
      print("still "+stillname)
    
    camera.wait_recording(20)
    
    if (debug):
      print("video ending "+videoname)

    now = time.gmtime()
    videoname = videocachedir+getFileName(now,'h264')  
    camera.split_recording(videoname)
    if (debug):
      print("video started "+videoname)

    camera.wait_recording(30)
    
    if (debug):
      print("video ending "+videoname)

    now = time.gmtime()
    videoname = videocachedir+getFileName(now,'h264')  
    camera.split_recording(videoname)
    if (debug):
      print("video started "+videoname)


    
    
    #Loop
    #while keyboard test.
      #camera.wait_recording(10)
    
      #Check the buttons
      
      #Save any button presses in the file system
      #Check the time : If  photo should be taken 
        #Generate file name photos/2014-01/15/17/56-59
        #Take
  
      #Check the time : If video should change name
        #Generate file name videobuffer/2014-01-15-17-56-59
        #Change video file
        #Check the file system to see if there any videos more than 10 minutes older  than  ten minutes without an event and eith delete or move
  
  
  
  camera.stop_recording()

