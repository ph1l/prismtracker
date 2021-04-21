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

"""Various Beacon Algorithms"""

import logging

logger = logging.getLogger(__name__)

class BeaconAlgorithmInterval():
    """ Interval Beacon Algorithm """

    def __init__(self, gps_i, interval=600):
        self.gps_i = gps_i
        self.interval = interval

        self.last_position = {'report_time': 0}


    def check(self):
        """ check to see if we should send a position report now """

        gps_timestamp = self.gps_i.get_timestamp()

        if gps_timestamp < self.last_position['report_time'] + self.interval:
            logger.debug("Not sending a report, interval has not expired")
            return False

        self.last_position['report_time'] = gps_timestamp
        return True


class BeaconAlgorithmSmart():
    """ Smart Beacon Algorithm """

    def __init__(self, gps_i, min_interval=60, max_interval=1200):
        self.last_position = {
                'report_time':  0,
                'latitude': 0,
                'longitude': 0,
                'course': 0,
            }

        self.min_interval = min_interval
        self.max_interval = max_interval

        self.gps_i = gps_i


    def check(self):
        """ check to see if we should send a position report now """

        gps_timestamp = self.gps_i.get_timestamp()

        if gps_timestamp < self.last_position['report_time'] + self.min_interval:
            logger.debug("Not sending a report, min_interval has not expired")
            return False

        (gps_latitude, gps_longitude) = self.gps_i.get_position()
        (gps_course, gps_speed) = self.gps_i.get_course_and_speed()

        if gps_timestamp > self.last_position['report_time'] + self.max_interval:
            logger.info("Sending report due to max_interval timeout...")

        else:
            logger.debug("got pos %s, %s course %s and speed %s",
                    gps_latitude, gps_longitude, gps_course, gps_speed
                )

            speed_ratio = gps_speed/47.79 # 55 mph

            if gps_speed > 4.34: # 5 mph
                course_diff = abs(gps_course - self.last_position['course'])
                if course_diff > 180:
                    course_diff = 360 - course_diff
                course_ratio = course_diff/45.0
            else:
                course_ratio = 0

            combined_ratio = (speed_ratio+course_ratio)/2.0
            if combined_ratio > 1.0:
                combined_ratio = 1.0

            logger.debug("(speed ratio: %s + course ratio: %s)/2.0 = combined ratio: %s",
                    speed_ratio, course_ratio, combined_ratio
                )

            if (gps_timestamp < self.last_position['report_time'] + self.max_interval
                    - (float(combined_ratio) * (self.max_interval-self.min_interval))
                ):
                return False
            logger.info("Sending report due to combined ratio: %s", combined_ratio)

        logger.info("last report: %d secs ago", gps_timestamp - self.last_position['report_time'])

        self.last_position['report_time'] = gps_timestamp
        self.last_position['latitude'] = gps_latitude
        self.last_position['longitude'] = gps_longitude
        self.last_position['course'] = gps_course

        return True


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
