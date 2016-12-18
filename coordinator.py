#!/usr/bin/env python
# coding: latin-1

# tinyhan coordinator
# (C) 2016-12 Folkert Huizinga <folkerthuizinga@gmail.com>

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
import struct
import serial
import argparse
import json
import daemon
import paho.mqtt.client as mqtt

INTERVAL = 10
NMETRICS = 8
UUID = 0x8000736d65746572L

def message(client, device, msg):
    """
    Handles incomming requests
    @param client, the active mqtt client
    @param device, the serial device
    @param msg, the incomming message
    """
    print msg.topic + " " + str(msg.payload)


if __name__ == "__main__":

    with daemon.DaemonContext():
        device          = serial.Serial()
        device.baudrate = 115200
        device.bytesize = serial.SEVENBITS
        device.parity   = serial.PARITY_EVEN
        device.stopbits = serial.STOPBITS_ONE
        device.xonxoff  = 0
        device.rtscts   = 0
        device.timeout  = 100
        device.port     = '/dev/ttyACM0'

        client = mqtt.Client(client_id="coordinator", clean_session=True,
                             userdata=device, protocol=mqtt.MQTTv31)

        client.on_message = message
        client.connect("127.0.0.1", 1883, 60)
        client.loop_start()
        client.subscribe(("zhc/coordinator", 2))

        client.publish("zhc/log/new", 
                payload=json.dumps({'uuid':UUID, 'interval':INTERVAL, 'nmetrics': NMETRICS}), 
                retain=False, qos=2)

        try:
            device.open()
        except IOError as e:
            sys.exit("Error: {}".format(e))
        
        while True:
            try:
                magic = 0
                stream = ['\x00'] * 4
                while magic != 0x55423CE7:
                    stream.append(device.read())
                    stream.pop(0)
                    magic = struct.unpack('I', ''.join(stream))[0]
                hdr = ''.join(stream) + device.read(12)
                _, size, type, uuid = struct.unpack('IHHQ', hdr)
                data = device.read(size)

            except IOError as e:
                print "Error: {}".format(e)
                continue

            if type == 1:
                telegram = struct.unpack('fffffffB', data)
                values = map(lambda x: round(x, 3), list(telegram))
                client.publish("zhc/log/submit",
                        payload=json.dumps({'uuid':uuid, 'values':values}),
                        retain=False, qos=0)


