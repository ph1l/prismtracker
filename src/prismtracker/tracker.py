# prismtracker - An APRS Tracker Daemon
# Copyright 2021 Philip J Freeman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""An APRS Tracker Daemon"""

import argparse
import logging
import time

from prismtracker import aprs, broadcast, gps

def main():
    """ main daemon entrypoint """

    parser = argparse.ArgumentParser()

    parser.add_argument('--call',
            help="Callsign with SSID suffix",
            required=True,
        )
    parser.add_argument('--beacon',
            help='Broadcast with AX.25 beacon cmd',
            action='store_true',
        )
    parser.add_argument('--beacon-port',
            help="AX.25 beacon port",
            default="ax0",
        )
    parser.add_argument('--aprsis',
            help='Broadcast to APRS-IS',
            action='store_true',
        )
    parser.add_argument('--aprsis-passcode',
            help='Passcode for connecting to APRS-IS',
            default='',
        )
    parser.add_argument('--path',
            help="via path",
            default="WIDE1-1,WIDE2-1",
        )
    parser.add_argument('--gps',
            help='GPS mode (gpsd, etc...)',
            default='gpsd',
        )
    parser.add_argument('--symbol-table',
            help='APRS display symbol table',
            default='/',
        )
    parser.add_argument('--symbol',
            help='APRS display symbol character code',
            default='>',
        )
    parser.add_argument('--timestamp',
            help='include timestamp in position report',
            action='store_true',
        )
    parser.add_argument('--altitude',
            help='include altitude in position report',
            action='store_true',
        )
    parser.add_argument('--interval',
            help='minimum seconds between position reports',
            type=int,
            default=0,
        )
    parser.add_argument('--loglevel',
            help='log level (debug, info, warning, error)',
            default="info",
        )

    opts = parser.parse_args()

    logging.basicConfig(
            level=getattr(logging, opts.loglevel.upper()),
            format='%(levelname)s %(name)s.%(funcName)s:%(lineno)d - %(message)s'
        )

    logger = logging.getLogger(__name__)

    # Setup GPS Interface
    if opts.gps == 'gpsd':
        gps_i = gps.GpsInterfaceGpsd()
    else:
        logger.error("Unknown GPS interface: %s", opts.gps)
        return 2

    # Setup broadcasters
    bcasts = []
    if opts.beacon:
        bcast = broadcast.BroadcastAx25Beacon(ax25_port=opts.beacon_port)
        bcasts.append(bcast)
    if opts.aprsis:
        bcast = broadcast.BroadcastAprsIs(opts.call, opts.aprsis_passcode)
        bcasts.append(bcast)

    while 1:

        while 1:
            try:
                gps_i.update()
            except gps.GpsInterfaceNotReady as error:
                logger.warning("GPS Not Ready: %s", error)
                time.sleep(5)
                continue
            break

        # Build the APRS Packet
        path = []
        if len(opts.path) > 0:
            path.extend(opts.path.split(','))

        (gps_latitude, gps_longitude) = gps_i.get_position()
        (gps_course, gps_speed) = gps_i.get_course_and_speed()

        frame = aprs.PositionReport(
                source = opts.call,
                destination = aprs.APP_DESTINATION,
                path = path,
                table = opts.symbol_table,
                symbol = opts.symbol,
                lat = gps_latitude,
                lon = gps_longitude,
                course = gps_course,
                speed = gps_speed,
            )

        if opts.timestamp:
            gps_time = gps_i.get_timestring()
            frame.add_timestamp(
                    hour = int(gps_time[11:13]),
                    minute = int(gps_time[14:16]),
                    second = int(gps_time[17:19]),
                )

        if opts.altitude:
            gps_altitude = gps_i.get_altitude()
            frame.add_altitude(gps_altitude)

        logger.info("APRS Frame: %s", frame)

        # Broadcast It!
        for bcast in bcasts:
            bcast.send_frame(frame)

        if opts.interval == 0:
            break
        time.sleep(opts.interval)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
