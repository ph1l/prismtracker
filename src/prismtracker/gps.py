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

""" GPS Driver abstraction """

import logging
import time

import gpsd

logger = logging.getLogger(__name__)

GPSD_RESPONSE_STATUS_MAP = ["No value", "No fix", "2D fix", "3D fix"]

class GpsInterfaceNotReady(Exception):
    """ For notifying callers that the GPS isn't ready """


class GpsInterface:
    """
    Base class for GPS Drivers.

    These drivers should operate like this:

        gps_i = GpsInterfaceType()
        while 1:
            try:
                gps_i.update() # stages latest status from underlying driver
            except GpsInterfaceNotReady as e:
                print("Still waiting for fix: {}".format(e))
                time.sleep(1)
                continue
            break
        (lat, lon) = gps_i.get_position()
        (course, speed) = gps_i.get_course_and_speed()

        print(
                "lat: {:010.7f}, lon: {:011.7f}, "
                "course: {:06.2f}, speed: {:06.2f}m/s".format(
                        lat, lon, course, speed
                    )
            )
    """

    def update(self):
        """
        stages the latest data in the driver for retrival or raises a
        GpsInterfaceNotReady exception
        """
        raise NotImplementedError("update() not implemented")


    def get_position(self):
        """
        returns the current decimal position as a tuple
        """
        raise NotImplementedError("get_position() not implemented")


    def get_course_and_speed(self):
        """
        returns the current course in degrees and speed in knots
        """
        raise NotImplementedError("get_course_and_speed() not implemented")


    def get_altitude(self):
        """
        returns the current altitude in feet
        """
        raise NotImplementedError("get_altitude() not implemented")


    def get_timestring(self):
        """
        returns the current date and time as a string
        """
        raise NotImplementedError("get_timestring() not implemented")


    def get_timestamp(self):
        """ convert GPS Zulu timestring to datetime object """

        return time.mktime(time.strptime(self.get_timestring(), '%Y-%m-%dT%H:%M:%S.%fZ'))


    def stop(self):
        """
        hook for adding cleanup of the GPS Driver
        """



class GpsInterfaceGpsd(GpsInterface):
    """ GPSd GPS Driver using gpsd-py3 package """

    def __init__(self):
        self.packet = None
        gpsd.connect()


    def update(self):
        self.packet = gpsd.get_current()
        if self.packet.mode < 3:
            raise(GpsInterfaceNotReady("waiting for Fix (current mode: {})".format(
                    GPSD_RESPONSE_STATUS_MAP[self.packet.mode]
                )))


    def get_position(self):
        return (
                self.packet.lat,
                self.packet.lon
            )


    def get_course_and_speed(self):
        return (
                self.packet.movement()['track'],
                self.packet.movement()['speed']*1.943844 # M/s -> kts
            )


    def get_altitude(self):
        return self.packet.altitude() * 3.28084 # M -> ft


    def get_timestring(self):
        return self.packet.time


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
