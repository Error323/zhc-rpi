#!/usr/bin/env python
# coding: latin-1

# opentherm gateway
# (C) 2016-11 Folkert Huizinga <folkerthuizinga@gmail.com>

#    This package is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; version 2 dated June, 1991.

#    This package is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this package; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
#    02111-1307, USA.

import os
import sys
import time
import serial
import argparse
import json
import daemon
import paho.mqtt.client as mqtt

UUID = int('boiler'.encode('hex'), 16)

def u16(x):
    """
    Converts 2 bytes to unsigned int
    @param x, the 2 bytes
    """
    return x


def s16(x):
    """
    Converts 2 bytes to signed int
    @param x, the 2 bytes
    """
    if x&0x8000:
        return -(0x10000 - x)
    else:
        return x


def f88(x):
    """
    Converts fixed point 8.8 to float
    @param x, the 2 bytes
    """
    if x&0x8000:
        return round(-(0x10000 - x) / 256.0, 2)
    else:
        return round(x / 256.0, 2)


MSGID = {
    0:   (u16, "Status"),
    1:   (f88, "Control Setpoint"),
    18:  (f88, "CH-Pressure"),
    19:  (f88, "DHW Flow-rate"),
    25:  (f88, "Boiler Temperature"),
    26:  (f88, "DHW Temperature"),
    33:  (s16, "Exhaust Temperature"),
    116: (u16, "Burner Starts"),
    117: (u16, "CH Pump Starts"),
    118: (u16, "DHW Pump Starts"),
    119: (u16, "DHW Burner Starts"),
    120: (u16, "Burner Operation Hours"),
    121: (u16, "CH Pump Operation Hours"),
    122: (u16, "DHW Pump Operation Hours"),
    123: (u16, "DHW Burner Operation Hours")
}


def sighandler(signum, frame):
    sys.exit("Trapped signal '%d' exit now" % (signum))


def message(client, device, msg):
    """
    Handles incomming requests
    @param client, the active mqtt client
    @param device, the serial device
    @param msg, the incomming message
    """
    print msg.topic + " " + str(msg.payload)


def index(key):
    keys = MSGID.keys()
    keys.sort()
    keys.index(key)
    return keys.index(key) + 7


def parse(msg, values):
    """
    Parses boiler messages
    @param msg, the incomming message
    @param values, a running list of all values
    """

    # Filter such that we only get boiler msgs)
    if msg[0] != 'B':
        return

    frame = int(msg[1:], 16)
    if bin(frame).count("1") & 1:
        print "Error: Invalid msg {}".format(msg)
        return

    msg_type = (frame >> 28) & 0x7
    data_id = (frame >> 16) & 0xff
    data_val = frame & 0xffff

    if data_id in MSGID:
        status, val = MSGID[data_id]
        if data_id == 0:
            for i in range(8):
                values[i] = (val >> i) & 1
        else:
            values[index(data_id)] = val


if __name__ == "__main__":

    with daemon.DaemonContext():
        signal.signal(signal.SIGTERM, sighandler)
        signal.signal(signal.SIGINT, sighandler)

        device          = serial.Serial()
        device.baudrate = 9600
        device.bytesize = serial.SEVENBITS
        device.parity   = serial.PARITY_EVEN
        device.stopbits = serial.STOPBITS_ONE
        device.xonxoff  = 0
        device.rtscts   = 0
        device.timeout  = 20
        device.port     = '/dev/ttyUSB0'

        client = mqtt.Client(client_id="otgw", clean_session=True,
                             userdata=device, protocol=mqtt.MQTTv31)

        client.on_message = message
        client.connect("127.0.0.1", 1883, 60)
        client.loop_start()
        client.subscribe(("zhc/otgw", 2))

        try:
            device.open()
        except IOError as e:
            sys.exit("Error: {}".format(e))
            
        t = time.time()
        line = ""
        while (True):
            try:
                line = device.readline()
            except IOError as e:
                print "Error: {}".format(e)
                continue

            parse(line)
            
            if time.time() - t >= 10.0:
                t += 10.0
                client.publish("zhc/log/submit", 
                    payload=json.dumps({'uuid':UUID, 'values':values}), 
                    retain=False, qos=0)
