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

""" Broadcast Driver abstraction """

import logging
import subprocess

import aprslib

logger = logging.getLogger(__name__)

class BroadcastError(Exception):
    """ For notifying callers that the broadcast failed """


class Broadcast:
    """
    Base class for Broadcast Drivers.

    These drivers should operate like this:

        aprsframe = aprs.PositionReport(...)

        bcast_i = BroadcastType(...)
        while 1:

            aprsframe = aprs.BeaconType(...)

            bcast_i.send_frame(aprsframe)

            time.sleep(10 * 60)
    """

    def send_frame(self, frame):
        """
        broadcast a frame or raise a BroadcastError exception
        """
        raise NotImplementedError("send_frame() not implemented")


class BroadcastAx25Beacon(Broadcast):
    """ AX.25 Beacon Broadcast Driver """

    def __init__(self, ax25_port):
        self.ax25_port = ax25_port


    def send_frame(self, frame):
        cmd = ["/usr/sbin/beacon"]
        cmd.extend(("-c", frame.source))
        if len(frame.path) > 0:
            cmd.extend(("-d", "{} via {}".format(
                    frame.destination,
                    " ".join(frame.path)
                )))
        else:
            cmd.extend(("-d", frame.destination))
        cmd.extend(("-s", self.ax25_port))
        cmd.append(frame.info)

        logger.debug("EXEC: %s", cmd)
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode > 0:
            logger.error("run(%s) returned %d; stdout=%s, stderr=%s",
                    cmd, result.returncode, result.stdout, result.stderr
                )
            raise BroadcastError("{:s} returned code {:d}".format(cmd[0], result.returncode))
        logger.info("frame sent %s", frame)


class BroadcastAprsIs(Broadcast):
    """ APRS-IS Broadcast Driver """

    def __init__(self, login, passcode):
        self.login = login
        self.passcode = passcode

        self.connection = aprslib.IS(self.login, self.passcode, port=14580)
        self.connection.connect()

    def send_frame(self, frame):
        self.connection.sendall(str(frame))
        logger.info("frame sent: %s", frame)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
