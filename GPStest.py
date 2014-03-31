from GPSController import *
#create controller
gpsc = GpsController()

#start controller
gpsc.start()

#read latitude and longitude
print gpsc.fix.latitude
print gpsc.fix.longitude
print gpsc.fix.time

#stop controller
gpsc.stopController()
gpsc.join()
