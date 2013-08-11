#!/usr/bin/env python2.7
# script by Alex Eames http://RasPi.tv
import RPi.GPIO as GPIO
import sys
import os
import time
from time import sleep

front_led_status = sys.argv[-1]
if front_led_status == "0":
    print "front LED off"
    front_led_status = 0

streaming_on = 0
streaming_file = "/home/pi/streaming.txt"
time_off = 0

GPIO.setmode(GPIO.BCM)

# GPIO 23 set up as input, pulled up to avoid false detection.
# wired to connect to GND on button press.
# So we'll be setting up falling edge detection 
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# GPIO 24 set up as an input, pulled down, connected to 3V3 on button press
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Set up GPIO 5 for camera LED control and rear LED control
GPIO.setup(5, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)

def write_streaming_status(streaming_on):
    vrnw = open(streaming_file, 'w')
    vrnw.write(str(streaming_on))
    vrnw.close()

def check_streaming_status():
# read file streaming_file, make into int() set streaming_on equal to it
    vrn = open(streaming_file, 'r')
    streaming_on = int(vrn.readline())
    #print "streaming_on is %d" % streaming_on
    vrn.close()
    return streaming_on

# threaded callback function runs in another thread when event is detected
# this increments variable rec_num for filename and starts recording
def stream_button(channel):
    global time_off
    time_now = time.time()
    if (time_now - time_off) >= 0.3:
        streaming_status = check_streaming_status()
        if streaming_status == 0:
            write_streaming_status(1)
            print "stream button pressed"
            if front_led_status != 0:
                GPIO.output(5, 1)
            GPIO.output(22, 1)
    time_off = time.time()

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
    flash(0.05,50)
    GPIO.cleanup()
    os.system("sudo halt")
    sys.exit()

try:
    write_streaming_status(0)
except:
    print "couldn't write streaming status"
    sys.exit()

# when a falling edge is detected on blue stream button port 23 stream_button() will be run
GPIO.add_event_detect(23, GPIO.FALLING, callback=stream_button)

try:
    while True:
        # this will run until black button attached to 24 is pressed, then 
        # if pressed long, shut program, if pressed very long shutdown Pi
        # stop recording and shutdown gracefully
        print "Waiting for button press" # rising edge on port 24"
        GPIO.wait_for_edge(24, GPIO.RISING)
        #print "Stop button pressed"

        time_now = time.time()
        if (time_now - time_off) >= 0.3:
            streaming_status = check_streaming_status()
            if streaming_status == 1:
                write_streaming_status(0)
                print "Stop button pressed"
                GPIO.output(5, 0)
                GPIO.output(22, 0)
        time_off = time.time()

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
            write_streaming_status(2)   # 2 will close the host program
            GPIO.cleanup()
            sys.exit()

        if GPIO.input(24):
            if i >= 59:
                shutdown()

finally:
    write_streaming_status(2)
    GPIO.cleanup()       # clean up GPIO on exit
