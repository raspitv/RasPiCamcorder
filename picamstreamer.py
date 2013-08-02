#!/usr/bin/env python2.7
# script by Alex Eames http://RasPi.tv

from subprocess import call
import sys
import time

front_led_status = sys.argv[-1]
if front_led_status == "0":
    print "front LED off"
    front_led_status = 0

streaming_on = 0
streaming_file = "/home/pi/streaming.txt"
if front_led_status == 0:
    sudo_file = "sudo python /home/pi/picamstream-sudo.py 0 &"
else:
    sudo_file = "sudo python /home/pi/picamstream-sudo.py &"

stream = "raspivid -o - -t 9999999 -w 640 -h 360 -fps 25|cvlc stream:///dev/stdin --sout '#standard{access=http,mux=ts,dst=:8090}' :demux=h264 &"

# you can change -w and -h numbers for whatever suits your network.
# Depending on what I'm streaming to, mine can cope with 720p, 
# which is -w 1280 -h 720

def stream_video():
    print "starting streaming\n%s" % stream
    call ([stream], shell=True)

def stop_stream():
    print "stopping streaming"
    call (["pkill raspivid"], shell=True)
    call (["pkill cvlc"], shell=True)

def check_streaming_status():
# read file streaming_file, make into int() set streaming_on equal to it
    vrn = open(streaming_file, 'r')
    streaming_on = int(vrn.readline())
    #print "streaming_on is %d" % streaming_on
    vrn.close()
    return streaming_on

def write_streaming_status(streaming_on):
    vrnw = open(streaming_file, 'w')
    vrnw.write(str(streaming_on))
    vrnw.close()

try:
    write_streaming_status(0)
except:
    print "couldn't write streaming status"
    sys.exit()

call ([sudo_file], shell=True)
   
previous_streaming_on = 0
counter = 0

#have a file containing the streaming_on variable value
while True:
    streaming_on = check_streaming_status()
    #print "streaming status = %d" % streaming_on

    if streaming_on != previous_streaming_on:
        if streaming_on == 1:
            stream_video()
        elif streaming_on == 0:
            stop_stream()
        else:
            stop_stream()
            print "Closing picamstreamer.py"
            sys.exit()
    if counter % 50 == 0:
        print "streaming status = %d" % streaming_on  
    previous_streaming_on = streaming_on
    counter += 1
    time.sleep(0.1)
