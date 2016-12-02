#!/usr/bin/env python
# coding: latin-1

# opentherm gateway timestore logging
# (C) 2016-11 Folkert Huizinga <folkerthuizinga@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import daemon
import argparse
import json
import paho.mqtt.client as mqtt
from timestore import Client, TimestoreException

MSG = { 
    0: 0,
    1: 8,
    18: 9,
    19: 10,
    25: 11,
    26: 12,
    33: 13,
    116: 14,
    117: 15,
    118: 16,
    119: 17,
    120: 18,
    121: 19,
    122: 20,
    123: 21
}

def message(client, updates, msg):
    """
    Handles incomming requests

    @param client, the active mqtt client
    @param _, empty
    @param msg, the incomming message
    """
    mid = int(msg.topic[msg.topic.rfind('/')+1:])
    load = json.loads(msg.payload)
    value = load['value']

    if mid == 0:
        for i in range(8):
            updates[0][i] = (value >> i) & 1
    else:
        updates[0][MSG[mid]] = value


def get_configuration():
    """
    Returns a populated configuration
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default="localhost:8080",
        help='Host:Port where timestore is running')
    parser.add_argument('--key', type=str,
        help='Timestore key')

    return parser.parse_args()


if __name__ == "__main__":
    boiler_values = [0.0] * 22
    boiler_node = int('boiler'.encode('hex'), 16)
    config = get_configuration()
    ts = Client(config.host)

    client = mqtt.Client(client_id="log", clean_session=True,
                         userdata=[boiler_values],
                         protocol=mqtt.MQTTv31)
    client.on_message = message
    client.connect("127.0.0.1", 1883, 60)
    client.loop_start()
    client.subscribe(("zhc/boiler/+", 2))

    while True:
        ts.submit_values(boiler_node, boiler_values, key=config.key)
        time.sleep(1)
