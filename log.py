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


def message(client, user, msg):
    """
    Handles incomming requests

    @param client, the active mqtt client
    @param user, user data (config and timestore objects)
    @param msg, the incomming message
    """
    cfg, ts = user
    topic = msg.topic.split('/')[-1]
    data = json.loads(msg.payload)

    # if this is a new node we first register it with the database
    if topic == 'new':
        try:
            node = ts.get_node(node_id=data['uuid'], key=cfg.key)
        except TimestoreException:
            node = {
                'interval' : data['interval'],
                'decimation' : [20, 6, 6, 4, 7],
                'metrics' : [{'pad_mode': 0, 'downsample_mode': 0}] * data['nmetrics']
            }
            ts.create_node(data['uuid'], node, key=cfg.key)

    # submit values otherwise
    elif topic == 'submit':
        try:
            ts.submit_values(data['uuid'], data['values'], key=cfg.key)
        except TimestoreException:
            pass


def get_configuration():
    """
    Returns a populated configuration
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default="localhost:8080",
        help='host:port where timestore is running')
    parser.add_argument('--key', type=str,
        help='timestore admin key')

    return parser.parse_args()


if __name__ == "__main__":
    with daemon.DaemonContext():
        config = get_configuration()
        ts = Client(config.host)

        client = mqtt.Client(client_id="log", clean_session=True,
                             userdata=(config, ts),
                             protocol=mqtt.MQTTv31)
        client.on_message = message
        client.connect("127.0.0.1", 1883, 60)
        client.subscribe(("zhc/log/+", 2))
        client.loop_forever()
