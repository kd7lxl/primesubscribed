#!/usr/bin/env python
#
# Copyright 2014 Tom Hayward <tom@tomh.us>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import MySQLdb
import textwrap
import urllib2

from settings import *


def get_prime_lineup(primeip=PRIME):
    primeurl = "http://" + primeip + "/lineup.json"
    response = urllib2.urlopen(primeurl)
    return json.load(response)


def index_lineup(lineup):
    indexed = {}
    for channel in lineup:
        indexed[int(channel["GuideNumber"])] = channel
    return indexed


def get_myth_channels():
    cur.execute("""SELECT chanid, channum, callsign, name, visible
                   FROM channel
                   WHERE sourceid = %s""", (MYTHVIDEOSOURCE,))
    channels = {}
    columns = tuple([d[0].decode('utf8') for d in cur.description])
    for row in cur.fetchall():
        rowdict = dict(zip(columns, row))
        channels[int(rowdict['channum'])] = rowdict
    return channels


if __name__ == "__main__":
    db = MySQLdb.connect(**MYTHMYSQL)
    cur = db.cursor()

    lineup = index_lineup(get_prime_lineup())
    ids = []
    for channum, chan in get_myth_channels().items():
        if bool(chan['visible']) and (
            not lineup.get(channum)            # Channel is not in lineup
            or lineup.get(channum).get("DRM")  # Channel has CCI copy protection
        ):
            ids.append(int(chan['chanid']))
            #print "%3d" % channum, chan['callsign'].ljust(10), chan['name']

    if ids:
        query = textwrap.fill(
            "UPDATE `channel` SET `visible`='0' "
            "WHERE `chanid` IN (%s);" % ', '.join(str(x) for x in ids), 80)
        print query
        if UPDATE:
            cur.execute(query)
    else:
        print "No update needed."
