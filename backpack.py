import picamera
import time


with picamera.PiCamera() as camera:


  #Power up
  #camera.resolution = (1920, 1080) #1080P Full HD 1920x1080
  #camera.start_preview()
  time.sleep(2)
  start = time.time()

  # ('img{timestamp:%Y-%m-%d-%H-%M}.jpg'):
  
  #calc name
  #camera.start_recording('foo.h264')
  
  #camera.capture('foo.jpg', use_video_port=True)
  #camera.wait_recording(10)
  #camera.stop_recording()

  
  #Start video
  #Set the next time a photo should be taken
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



