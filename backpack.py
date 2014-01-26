import picamera
import time
import os


outputbasedir =  os.path.expanduser('~/BPOA/') 
videocachedir = outputbasedir+'videocache/'

startuppause = 5
timelapsedir = os.path.expanduser('~/timelapse')

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
  camera.resolution = (1920, 1080) #1080P Full HD 1920x1080
  #camera.start_preview()
  time.sleep(startuppause)
  start = time.gmtime()

  
  #calc name
  camera.start_recording(videocachedir+getFileName(start,'h264'),  inline_headers=True)
  camera.wait_recording(startuppause)
  
  camera.capture(getFolderName(start,'jpg')+getFileName(start,'jpg'), use_video_port=True)
  camera.wait_recording(50)
  
  now =time.gmtime()
  camera.split_recording(videocachedir+getFileName(now,'h264'))
  camera.wait_recording(10)
  
  camera.capture(getFolderName(now,'jpg')+getFileName(now,'jpg'), use_video_port=True)
  camera.wait_recording(60)
  
  
  
  #Start video
  #Set the next time a photo should be takne
  #Set the next time the video should change name

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

