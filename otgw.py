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
from convert import *


UUID = int('cvsystem'.encode('hex'), 16)
MSGID = {
    0:   (u16, "Status"),                    # Master and Slave Status flags
    1:   (f88, "TSet"),                      # Control setpoint ie CH water temperature setpoint (°C)
    14:  (f88, "Max-rel-mod-level-setting"), # Maximum relative modulation level setting (%)
    16:  (f88, "TrSet"),                     # Room Setpoint (°C)
    17:  (f88, "Rel.-mod-level"),            # Relative Modulation Level (%)
    18:  (f88, "CH-Pressure"),               # Water pressure in CH circuit (bar)
    19:  (f88, "DHW-flow-rate"),             # Water flow rate in DHW circuit. (litres/minute)
    24:  (f88, "Tr"),                        # Room temperature (°C)
    25:  (f88, "Tboiler"),                   # Boiler flow water temperature (°C)
    26:  (f88, "Tdhw"),                      # DHW temperature (°C)
    27:  (f88, "Toutside"),                  # Outside temperature (°C)
    56:  (f88, "TdhwSet"),                   # DHW setpoint (°C) (Remote parameter 1)
    116: (u16, "Burner starts"),             # Number of starts burner
    117: (u16, "CH pump starts"),            # Number of starts CH pump
    118: (u16, "DHW pump/valve starts"),     # Number of starts DHW pump/valve
    119: (u16, "DHW burner starts"),         # Number of starts burner during DHW mode
    120: (u16, "Burner operation hours"),    # Number of hours that burner is in operation (i.e. flame on)
    121: (u16, "CH pump operation hours"),   # Number of hours that CH pump has been running
    122: (u16, "DHW pump operation hours"),  # Number of hours that DHW pump has been running or DHW valve has been opened
    123: (u16, "DHW burner operation hours") # Number of hours that burner is in operation during DHW mode
}


def message(client, device, msg):
    """
    Handles incomming requests
    @param client, the active mqtt client
    @param device, the serial device
    @param msg, the incomming message
    """
    print msg.topic + " " + str(msg.payload)


def index(key):
    """
    Computes deterministic index for MSGID. This is necessary as some of the
    messages pack multiple data points.
    @param key, the key to compute an index for
    """
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

    frame = int(msg[1:], 16)
    if bin(frame).count("1") & 1:
        print "Error: Invalid msg {}".format(msg)
        return

    msg_type = (frame >> 28) & 0x7
    data_id = (frame >> 16) & 0xff
    data_val = frame & 0xffff

    if data_id in MSGID:
        status, val = MSGID[data_id][1], MSGID[data_id][0](data_val)
        if data_id == 0:
            for i in range(8):
                values[i] = (val >> i) & 1
        else:
            values[index(data_id)] = val


if __name__ == "__main__":

    with daemon.DaemonContext():
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
            
        # Create logging database
        NMETRICS = len(MSGID) + 7
        INTERVAL = 10
        client.publish("zhc/log/new", 
                payload=json.dumps({'uuid':UUID, 'interval':INTERVAL, 'nmetrics': NMETRICS}), 
            retain=False, qos=2)

        values = [0.0] * (len(MSGID)+7)
        t = time.time()
        line = ""
        while True:
            try:
                line = device.readline()
            except IOError as e:
                print "Error: {}".format(e)
                continue

            parse(line, values)
            
            if time.time() - t >= INTERVAL:
                t += INTERVAL
                client.publish("zhc/log/submit", 
                    payload=json.dumps({'uuid':UUID, 'values':values}), 
                    retain=False, qos=0)
