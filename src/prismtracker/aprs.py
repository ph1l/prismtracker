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

""" APRS Packet generation and utilities """

import logging
import math

logger = logging.getLogger(__name__)

APP_DESTINATION = "APZFSM"

def base91_encode(num):
    """
    base91 encode a numeric value

    NOTE: this works for values up to 91**4
    """
    num_places=4
    out = ""
    while num_places > 0:
        num_places = num_places - 1
        out = out + chr(33+int(num / 91 ** num_places))
        num = (num % 91 ** num_places)
    return out


def compress_latitude(deg_in):
    """ base 91 encode latitude for APRS position report """
    return base91_encode(380926 * (90 - deg_in))


def compress_longitude(deg_in):
    """ base 91 encode longitude for APRS position report """
    return base91_encode(190463 * (180 + deg_in))


def compress_course_and_speed(deg, kts):
    """ base91 encode course and speed values """
    return "{:1s}{:1s}Y".format(
           chr(33+round(deg/4.0)),
           chr(33+round(math.log(kts + 1, 1.08))),
        )


class APRSFrame:
    """ Base class for APRS Frames """

    def __init__( self, source, destination, path):
        self.source = source
        self.destination = destination
        self.path = path
        self.info = ""

    def __repr__(self):
        full_path = [self.destination]
        full_path.extend(self.path)
        frame = "{}>{}:{}".format(
                self.source,
                ','.join(full_path),
                self.info
            )
        return frame

    def __bytes__(self):
        frame = self.__repr__()
        return frame.encode()


class PositionReport(APRSFrame):
    """
    APRS Compressed Position Report w/ optional timestamp
    """
    def _update_info(self):

        self.info = "".join((
                self.report_type,
                self.timestamp,
                self.table,
                compress_latitude(self.lat),
                compress_longitude(self.lon),
                self.symbol,
                self.course_and_speed,
                self.altitude
            ))


    def __init__(self, source, destination, path, table, symbol, lat, lon, course, speed):

        super().__init__(source, destination, path)

        self.table = table
        self.symbol = symbol
        self.lat = lat
        self.lon = lon
        self.course = course
        self.speed = speed

        self.report_type = "!"
        self.timestamp = ""
        self.altitude=""

        self.course_and_speed = compress_course_and_speed(course, speed)

        self._update_info()


    def add_timestamp(self, hour, minute, second):
        """ Add optional timestamp to the report """

        self.report_type = "/"
        self.timestamp = "{:02d}{:02d}{:02d}h".format(hour, minute, second)
        self._update_info()


    def add_altitude(self, alt):
        """ Add optional timestamp to the report """

        self.altitude = "/A={:06d}".format(round(alt))
        self._update_info()


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
