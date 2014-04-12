from gps import *
import time
import threading
import math
import os

class GpsController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
        self.running = False
   
    def run(self):
        self.running = True
        while self.running:
            # grab EACH set of gpsd info to clear the buffer
            self.gpsd.next()

    def stopController(self):
        self.running = False
 
    @property
    def fix(self):
        return self.gpsd.fix

    @property
    def utc(self):
        return self.gpsd.utc

    @property
    def satellites(self):
        return self.gpsd.satellites

if __name__ == '__main__':
    # create the controller
    gpsc = GpsController() 
    try:
        # start controller
        gpsc.start()
        while True:
            
            if (gpsc.fix.latitude):
                print "latitude ", gpsc.fix.latitude
                print "longitude ", gpsc.fix.longitude
                print "altitude (m)", gpsc.fix.altitude
            
            if gpsc.utc and gpsc.utc<>"None":
                print "time utc ", gpsc.utc #, " + ", gpsc.fix.time
                
                sattime = time.mktime(time.strptime(gpsc.utc, "%Y-%m-%dT%H:%M:%S.000Z"))
                print("sattime =", sattime)
                print("time.time =", time.time())
                if (time.time() < sattime):
                    print "setting time"
                    os.system('date -s %s' % gpsc.utc)

                    
                
            #2014-03-29T17:33:31.000Z

            #print "eps ", gpsc.fix.eps
            #print "epx ", gpsc.fix.epx
            #print "epv ", gpsc.fix.epv
            #print "ept ", gpsc.gpsd.fix.ept
            #print "speed (m/s) ", gpsc.fix.speed
            #print "climb ", gpsc.fix.climb
            #print "track ", gpsc.fix.track
            #print "mode ", gpsc.fix.mode
            #print "sats ", gpsc.satellites
            time.sleep(0.5)

    #Ctrl C
    except KeyboardInterrupt:
        print "User cancelled"

    #Error
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise
        
    finally:
        print "Stopping gps controller"
        gpsc.stopController()
        #wait for the thread to finish
        gpsc.join()
     
    print "Done"
