#!/usr/bin/env python2.7
# script by Alex Eames http://RasPi.tv
# RasPiCamcorder stills camera mode with dropbox upload

# http://raspi.tv/?p=3424 and

# http://youtu.be/dSgj4bUFBCQ

import RPi.GPIO as GPIO
from subprocess import call
import subprocess
from time import sleep
import time
import sys
import os
import urllib2
import thread

front_led_status = sys.argv[-1]
if front_led_status == "0":
    print "front LED off"
    front_led_status = 0

GPIO.setmode(GPIO.BCM)

# GPIO 23 set up as input, pulled up to avoid false detection.
# wired to connect to GND on button press.
# So we'll be setting up falling edge detection
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# GPIO 24 set up as an input, pulled down, connected to 3V3 on button press
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Set up GPIO 5 for camera LED control and 22 for rear LED control
GPIO.setup(5, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)

# set initial variables
photo_rec_num = "photo_rec_num.txt"   
photo_rec_num_fp ="/home/pi/photo_rec_num.txt" # need full path if run from rc.local
base_vidfile = "raspistill -t 500 -o /home/pi/photo"
time_off = time.time()

def write_rec_num():
    vrnw = open(photo_rec_num_fp, 'w')
    vrnw.write(str(rec_num))
    vrnw.close()

def take_photo(rec_num):
    global time_off
    vidfile = base_vidfile + str(rec_num).zfill(5) + ".jpg"
    filename = "/home/pi/photo" + str(rec_num).zfill(5) + ".jpg"
    print "taking photo\n%s" % vidfile
    time_now = time.time()
    if (time_now - time_off) >= 0.3: # debounce
        time_off = time.time()
        if front_led_status != 0:
            GPIO.output(5, 1)
        GPIO.output(22, 1)
        call ([vidfile], shell=True)
        sleep(1)
        GPIO.output(5, 0)
        GPIO.output(22, 0)
        space_used()
        flash(0.1,3)

        enable_dropbox = internet()
        if enable_dropbox:
            print "\nsending %s to dropbox" % filename
            photofile = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload " + filename

            # put the dropbox upload into another thread 
            # so we can take more pictures without waiting for it

            threadname = "DB-Upload" + str(rec_num).zfill(5)
            try:
                thread.start_new_thread(db_thread, (threadname, photofile, ))
            except:
                print "Error: unable to start thread"
            flash(0.05,6)
        else:
            print "Unable to connect to dropbox. No internet?"
        flash(0.2,2)
        time_off = time.time() # for debounce

def db_thread(threadName, photofile):
    print "%s: %s" % (threadName, photofile)
    call ([photofile], shell=True)


def stop_recording(): # this may not be needed for stills
    global time_off
    time_off = time.time()
    print "stopping recording"
    GPIO.output(5, 0)
    GPIO.output(22, 0)
    call (["pkill raspistill"], shell=True)
    time_off = time.time() # repeat seems to help prevent false double records
    space_used()     # display space left on recording drive

def space_used():    # function to display space left on recording device
    output_df = subprocess.Popen(["df", "-Ph", "/dev/root"], stdout=subprocess.PIPE).communicate()[0]
    it_num = 0
    for line in output_df.split("\n"):
        line_list = line.split()
        if it_num == 1:
            storage = line_list
        it_num += 1
    print "\nCard size: %s,   Used: %s,    Available: %s,    Percent used: %s" % (storage[1], storage[2], storage[3], storage[4])
    percent_used = int(storage[4][0:-1])
    if percent_used > 95:
        print "Watch out, you've got less than 5% space left on your SD card!"

# threaded callback function runs in another thread when event is detected
# this increments variable rec_num for filename and takes a photo
def blue_button(channel):
    global rec_num
    time_now = time.time()
    if (time_now - time_off) >= 0.3:
        print "\nphoto button pressed"
        rec_num += 1
        write_rec_num()
        take_photo(rec_num)

def flash(interval,reps):
    for i in range(reps):
        GPIO.output(5, 1)
        GPIO.output(22, 1)
        sleep(interval)
        GPIO.output(5, 0)
        GPIO.output(22, 0)
        sleep(interval)

def shutdown():
    print "shutting down now"
    stop_recording()
    flash(0.05,50)
    GPIO.cleanup()
    os.system("sudo halt")
    sys.exit()

def internet():
    try:
        urllib2.urlopen("http://www.dropbox.com")
        enable_dropbox = 1
    except urllib2.URLError:
        enable_dropbox = 0
    return enable_dropbox

print "Make sure you have a button connected so that when pressed"
print "it will connect GPIO port 23 (pin 16) to GND (pin 6)\n"
print "You will also need a second button connected so that when pressed"
print "it will connect GPIO port 24 (pin 18) to 3V3 (pin 1)\n"

# when a falling edge is detected on port 23 blue_button() will be run
GPIO.add_event_detect(23, GPIO.FALLING, callback=blue_button)

# check rec_num from file
try:
    directory_data = os.listdir("/home/pi")
    if photo_rec_num in directory_data:

        # read file photo_rec_num, make into int() set rec_num equal to it
        vrn = open(photo_rec_num_fp, 'r')
        rec_num = int(vrn.readline())
        print "rec_num is %d" % rec_num
        vrn.close() 

    # if file doesn't exist, create it to avoid issues later
    else:
        rec_num = 0
        write_rec_num()

except:
    print("Problem listing /home/pi")
    flash(0.1,10)
    GPIO.cleanup()
    sys.exit()

try:
    while True:
        # this will run until button attached to 24 is pressed, then 
        # if pressed long, shut program, if pressed very long shutdown Pi
        # stop recording and shutdown gracefully
        print "Waiting for button press" # rising edge on port 24"
        GPIO.wait_for_edge(24, GPIO.RISING)
        print "Stop button pressed"

        # poll GPIO 24 button at 20 Hz continuously for 2 seconds
        # if at the end of that time button is still pressed, shut down
        # if it's released at all, break
        for i in range(60):
            if not GPIO.input(24):
                break
            sleep(0.05)

        if 25 <= i < 58:
            print "Closing program"
            flash(0.02,50) # interval,reps
            GPIO.cleanup()
            sys.exit()

        if GPIO.input(24):
            if i >= 59:
                shutdown()

except KeyboardInterrupt:
#    stop_recording()
    GPIO.cleanup()
    sys.exit()

# it would be really nice for headless use if we could have another led 
# for upload flash it in another thread while uploading to dropbox
# 
# have a demo mode which runs at lower res off mobile hotspot wifi
