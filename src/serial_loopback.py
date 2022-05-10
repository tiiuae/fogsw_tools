#!/usr/bin/env python3

"""
Performs a loopback test over serial. Helps identify serial communications
issues.

@author: Humaid AlQassimi (humaid.alqassimi@tii.ae)
"""

import time
import serial
from threading import Thread

# This is the message propagated through serial. I kept this slightly long to
# make sure we catch issue where sometimes random characters are dropped (which
# we do have!).
serialmessage = b'lorem ipsum dolor serial amet! Aperiam ducimus qui animi non deserunt ullam optio. Illo enim est sed est quae ab voluptatem\n'
serialDev = '/dev/px4serial'
ser = None

def serialWrite():
    ser.write(serialmessage)

def serialRead():
    line = ser.readline()
    if line == serialmessage:
        print("Successful!")
    else:
        print("Failed!")
        if len(line) == 0:
            print("No bytes were able to go through serial")
        else:
            print("Message received is not same as sent")
            print("Sent: " + repr(serialmessage.decode('ascii')))
            print("Got: " + repr(line.decode('ascii')))

def main():
    global ser
    ser = serial.serial_for_url(serialDev, timeout=2, baudrate=115200, rtscts=False, dsrdtr=False)
    threadWrite = Thread(target=serialWrite)
    threadRead = Thread(target=serialRead)
    threadRead.start()
    threadWrite.start()

    # Wait for the read to end
    threadRead.join()
    ser.close()

if __name__ == '__main__':
    main()


