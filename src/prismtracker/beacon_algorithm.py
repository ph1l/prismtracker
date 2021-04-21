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


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
