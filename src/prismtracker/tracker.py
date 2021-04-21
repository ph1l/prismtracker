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
import os
import time

import gpxpy

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
    parser.add_argument('--log-gpx',
            help='log gpx of position reports',
            default=None,
        )


    opts = parser.parse_args()

    logging.basicConfig(
            level=getattr(logging, opts.loglevel.upper()),
            format='%(levelname)s %(name)s.%(funcName)s:%(lineno)d - %(message)s'
        )

    # timezones are stupid -- so this isn't the best, but we're using strptime
    # to get a timestamp in seconds since epoc UTC from the GPS device.
    # strptime doesn't know about timezones apparently, so this hack gives us
    # the correct timestamp later in the `get_timestamp()' method of our gps
    # driver. *le' sigh*

    os.environ['TZ'] = 'Etc/UTC'
    time.tzset()

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

    # Setup GPX log
    if opts.log_gpx:
        try:
            with open(opts.log_gpx, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
        except:
            gpx = gpxpy.gpx.GPX()

        gpx_track_positions = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track_positions)
        gpx_segment_positions = gpxpy.gpx.GPXTrackSegment()
        gpx_track_positions.segments.append(gpx_segment_positions)

        gpx_track_broadcasts = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track_broadcasts)
        gpx_segment_broadcasts = gpxpy.gpx.GPXTrackSegment()
        gpx_track_broadcasts.segments.append(gpx_segment_broadcasts)


    while 1:

        while 1:
            try:
                gps_i.update()
            except gps.GpsInterfaceNotReady as error:
                logger.warning("GPS Not Ready: %s", error)
                time.sleep(5)
                continue
            break

        logger.debug("got timestamp %s seconds from time string: %s",
                gps_i.get_timestamp(), gps_i.get_timestring()
            )

        # Build the APRS Packet
        path = []
        if len(opts.path) > 0:
            path.extend(opts.path.split(','))

        (gps_latitude, gps_longitude) = gps_i.get_position()
        gps_altitude = gps_i.get_altitude()
        (gps_course, gps_speed) = gps_i.get_course_and_speed()

        # Log the position to GPX log track #1
        if opts.log_gpx is not None:
            gpx_segment_positions.points.append(gpxpy.gpx.GPXTrackPoint(
                    gps_latitude, gps_longitude,
                    elevation=gps_altitude * 0.3048, # ft -> meters
                    speed=gps_speed * 0.5144447 # kts -> M/s
                ))

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
            frame.add_altitude(gps_altitude)

        logger.info("APRS Frame: %s", frame)

        # Broadcast It!
        for bcast in bcasts:
            bcast.send_frame(frame)

        # Log the position broadcast to GPX log track #2
        if opts.log_gpx is not None:
            gpx_segment_broadcasts.points.append(gpxpy.gpx.GPXTrackPoint(
                    gps_latitude, gps_longitude,
                    elevation=gps_altitude * 0.3048, # ft -> meters
                    speed=gps_speed * 0.5144447 # kts -> M/s
                ))
            with open(opts.log_gpx, 'w') as gpx_file:
                gpx_file.write(gpx.to_xml(version="1.0"))

        if opts.interval == 0:
            break
        time.sleep(opts.interval)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
