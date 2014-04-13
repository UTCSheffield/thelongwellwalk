thelongwellwalk
===============

Raspberry Pi based system for recording and transmitting data from a lone long distance walker. Being built for http://thelongwellwalk.org/


# Status -Red = Disk space too low, audio & video will not record or its shutting down because the poweroff command has been entered
# Status -Blue = Video recording
# Status -cyan = Audio recording
# Status -green = Timelapse mode
# Status -Flashing Yellow = Disk space getting low
# Status -Flashing Red = Disk space too low, video will not record
# Status -Flashing Magenta = CPU too stressed

Turning on the power will start the scripts, and the light will turn on white ish for a few seconds then go Green (flashing Magenta because the start up process means the CPU is always running hard) it will settle to just green in a minute.

Hitting the Audio Button (This is the one marked in blue on the pair of buttons on the prototype) records audio and the light will go Cyan

The the other one will start video recording and the light will go Blue.

When videoing flashing Magenta is a warning that the RPi is struggling.

Clicking the Audio button once a second for at least 3 times will make the light go red and then go off entirely. give it a minute or so and the power can be turned off. 

