#!/usr/bin/python
# Raspberry Pi based system for recording and transmitting data from a lone long distance walker.
# Being built for http://thelongwellwalk.org/

#Import the supporting code we need
import time             # Time and Date functions
import RPi.GPIO as GPIO # Controls the GPIO for LEDs and Buttons

#Config


#GPIO Config
# Which GPIO pin does what job
videobutton = 11        # Video (currently rigged as momentary switch) 
audiobutton = 12        # Audio (no code so far)
poweroffbutton = 12        # Poweroff button (can be same as audio)

statusLED_R = 18          # Red LED, short wire on own
statusLED_G = 16          # Green LED middle length wire
statusLED_B = 15          # Blue LED short wire next to middle length
#The GND wire is the longest and is wired through a switch so it only shows when pressed



# GPIO setup
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD) # Use the standard RPi pin numbers

GPIO.setup(statusLED_R, GPIO.OUT)   # Set as Output
GPIO.setup(statusLED_G, GPIO.OUT)   # Set as Output
GPIO.setup(statusLED_B, GPIO.OUT)   # Set as Output



print("Red")
GPIO.output( statusLED_R, False)
GPIO.output( statusLED_G, True)
GPIO.output( statusLED_B, True)
time.sleep(2)


print("Blue")
GPIO.output( statusLED_R, True)
GPIO.output( statusLED_G, True)
GPIO.output( statusLED_B, False)
time.sleep(2)


print("Green")
GPIO.output( statusLED_R, True)
GPIO.output( statusLED_G, False)
GPIO.output( statusLED_B, True)
time.sleep(2)



print("White")
GPIO.output( statusLED_R, False)
GPIO.output( statusLED_G, False)
GPIO.output( statusLED_B, False)
time.sleep(2)


print("Yellow")
GPIO.output( statusLED_R, False)
GPIO.output( statusLED_G, False)
GPIO.output( statusLED_B, True)
time.sleep(2)


print("Cyan")
GPIO.output( statusLED_R, True)
GPIO.output( statusLED_G, False)
GPIO.output( statusLED_B, False)
time.sleep(2)


print("Magenta")
GPIO.output( statusLED_R, False)
GPIO.output( statusLED_G, True)
GPIO.output( statusLED_B, False)
time.sleep(2)



GPIO.output( statusLED_R, True) 
GPIO.output( statusLED_G, True)
GPIO.output( statusLED_B, True)
GPIO.cleanup()

