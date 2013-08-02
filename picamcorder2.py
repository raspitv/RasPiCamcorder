#!/usr/bin/env python2.7
# script by Alex Eames http://RasPi.tv
# needs RPi.GPIO 0.5.2 or later
# No guarantees. No responsibility accepted. It works for me.
# If you need help with it, sorry I haven't got time. I'll try and add more
# documentation as time goes by. But no promises.

import RPi.GPIO as GPIO
from subprocess import call
import subprocess
from time import sleep
import time
import sys
import os

front_led_status = sys.argv[-1]
if front_led_status == "0":
    print "front LED off"
    front_led_status = 0

GPIO.setmode(GPIO.BCM)

# GPIO 23 & 25 set up as input, pulled up to avoid false detection.
# Both ports are wired to connect to GND on button press.
# So we'll be setting up falling edge detection for both
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# GPIO 24 set up as an input, pulled down, connected to 3V3 on button press
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Set up GPIO 5 for camera LED control and rear LED control
GPIO.setup(5, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)

recording = 0
vid_rec_num = "vid_rec_num.txt"   
vid_rec_num_fp ="/home/pi/vid_rec_num.txt" # need full path if run from rc.local
base_vidfile = "raspivid -t 3600000 -o /home/pi/video"
time_off = time.time()

def write_rec_num():
    vrnw = open(vid_rec_num_fp, 'w')
    vrnw.write(str(rec_num))
    vrnw.close()

def start_recording(rec_num):
    global recording
    if recording == 0:
        vidfile = base_vidfile + str(rec_num).zfill(5)
        vidfile += ".h264  -fps 25 -b 15000000 -vs" #-w 1280 -h 720 -awb tungsten
        print "starting recording\n%s" % vidfile
        time_now = time.time()
        if (time_now - time_off) >= 0.3:
            if front_led_status != 0:
                GPIO.output(5, 1)
            GPIO.output(22, 1)
            recording = 1
            call ([vidfile], shell=True)
    recording = 0 # only kicks in if the video runs the full period

#### Quality VS length ###
# on long clips at max quality you may get dropouts
# -w 1280 -h 720 -fps 25 -b 3000000 
# seems to be low enough to avoid this 

def stop_recording():
    global recording
    global time_off
    time_off = time.time()
    print "stopping recording"
    GPIO.output(5, 0)
    GPIO.output(22, 0)
    call (["pkill raspivid"], shell=True)
    recording = 0
    space_used()     # display space left on recording drive

def space_used():    # function to display space left on recording device
    output_df = subprocess.Popen(["df", "-Ph", "/dev/root"], stdout=subprocess.PIPE).communicate()[0]
    it_num = 0
    for line in output_df.split("\n"):
        line_list = line.split()
        if it_num == 1:
            storage = line_list
        it_num += 1
    print "Card size: %s,   Used: %s,    Available: %s,    Percent used: %s" % (storage[1], storage[2], storage[3], storage[4])
    percent_used = int(storage[4][0:-1])
    if percent_used > 95:
        print "Watch out, you've got less than 5% space left on your SD card!"

# threaded callback function runs in another thread when event is detected
# this increments variable rec_num for filename and starts recording
def my_callback2(channel):
    global rec_num
    time_now = time.time()
    if (time_now - time_off) >= 0.3:
        print "record button pressed"
        rec_num += 1
        if recording == 0:
            write_rec_num()
            start_recording(rec_num)

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

print "Make sure you have a button connected so that when pressed"
print "it will connect GPIO port 23 (pin 16) to GND (pin 6)\n"
print "You will also need a second button connected so that when pressed"
print "it will connect GPIO port 24 (pin 18) to 3V3 (pin 1)\n"
#print "You will also need a third button connected so that when pressed"
#print "it will connect GPIO port 25 (pin 22) to GND\n"

# optional for when you're at the terminal
#raw_input("Press Enter when ready\n>")

# when a falling edge is detected on port 23 my_callback2() will be run
GPIO.add_event_detect(23, GPIO.FALLING, callback=my_callback2)

# when a falling edge is detected on port 25, my_callback() will be run
#GPIO.add_event_detect(25, GPIO.FALLING, callback=my_callback, bouncetime=500)

# check rec_num from file
try:
    directory_data = os.listdir("/home/pi")
    if vid_rec_num in directory_data:

        # read file vid_rec_num, make into int() set rec_num equal to it
        vrn = open(vid_rec_num_fp, 'r')
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
        stop_recording()

        # poll GPIO 24 button at 20 Hz continuously for 3 seconds
        # if at the end of that time button is still pressed, shut down
        # if it's released at all, break
        for i in range(60):
            if not GPIO.input(24):
                break
            sleep(0.05)

        if 25 <= i < 58:              # if released between 1.25 & 3s close prog
            print "Closing program"
            flash(0.02,50) # interval,reps
            GPIO.cleanup()
            sys.exit()

        if GPIO.input(24):
            if i >= 59:
                shutdown()

except KeyboardInterrupt:
    stop_recording()
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit

