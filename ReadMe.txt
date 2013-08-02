This Readme will contain some basic info about the RasPiCamcorder 2

But I haven't written it all yet, so, for the time being, you can pop over
to the http://RasPi.TV blog or YouTube and see some info about the project
there...

http://raspi.tv/?p=3424
and
http://youtu.be/dSgj4bUFBCQ

Buttons
=======
Basically you need a button connected between GPIO 23 and GND.
This is the "shoot video" button. (Mine is the blue one in this photo
http://raspi.tv/wp-content/uploads/2013/06/DSC_4467.jpg).

You also need a button between GPIO 24 and 3V3, which is the 
"stop shooting" button. It also doubles as the close program and shutdown
button depending on how long you press it for. (Mine is the black one in this
photo http://raspi.tv/wp-content/uploads/2013/06/DSC_4467.jpg).

LEDs
====
The camera LED is on GPIO 5. 
I have an additional LED (I wanted one on the back) on GPIO 22

Usage
=====
To run the program, you can type 

sudo python picamcorder2.py

Add a 0 (zero) if you want to disable the front LED 
(assuming you have added the necessary tweak to your config file)

sudo python picamcorder2.py 0


Setting up your Pi
==================

Setting up for auto start
-------------------------
Add this line to your /etc/rc.local

/home/pi/picamcorder.sh

Which runs a simple bash script on boot, allowing us a 10s time delay.

picamcorder.sh will have to be executable for this to work

chmod +x picamcorder.sh


The bash script picamcorder.sh just contains this...
sleep 10
sudo python /home/pi/picamcorder2.py &

...which slows things down enough to make it work and puts the process in the
background.


Setting up for small screen use
-------------------------------

sudo dpkg-reconfigure console-setup

lets you increase console font size for small screens


Setting up camera led manual control
------------------------------------

sudo nano /boot/config.txt

Add this line to your config.txt

disable_camera_led=1






########################Possible Future Development#############

# LED on the back to show recording --> DONE
# camera LED toggle to disable front LED, maybe with an argv argument? --> DONE
# leds flashing on program exit and shutdown --> DONE
# indication of how much recording time/disk space left --> DONE
# micro USB adaptor so Pi can be stood up at SD card end --> DONE
# 52mm thread adaptor for adding lenses --> DONE

# Stills button or button combo
# need a mount for it
# possibly pan and tilt
# possibly a rotating base for all-round work - either stepper or highly geared

######### it would be nice to have a third button for stills too
######### getting errors after adding port 25 for stills

## All parts referring to GPIO25 are commented out for now

# it seems that raspivid and raspistill don't play nicely together in the 
# same script, so had to remove the stills option for now

#def take_photo():
#    call (["raspistill -t 3000 -o test-pic.jpg"], shell=True)


#def my_callback(channel):
#    global rec_num
#    print "falling edge detected on 25"
#    if recording == 1:
#        stop_recording()
#        take_photo()
#        rec_num += 1
#        start_recording(rec_num)
#    else:
#        take_photo()

# Component list
# 1 model A Raspberry Pi
# 1 Raspberry Pi camera board
# 1 switching regulator board ###link###
# 1 Bluetooth serial adaptor ###link###
# battery & connectors
# female .1" pin headers
# wire
# 605 LED
# 150R 1206
# Cyntech case
# White tack
# hot glue gun
# buttons ###link###
# bit of stripboard
# 4x2 angled header

