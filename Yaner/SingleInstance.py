#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Yaner.

# Yaner - GTK+ interface for aria2 download mananger
# Copyright (C) 2010  Iven Day <ivenvd#gmail.com>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
    This file contains the super class of a single instance application
like Yaner, but could also be used by other programs.
"""

import socket

class SingleInstanceApp:
    "Single Instance Application"

    def __init__(self, temp_name):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            self.sock.bind('\0' + temp_name)
        except IOError:
            print "Another instance is already running."
            self.on_instance_exists()

    def on_instance_exists(self):
        """
        This method is called when an instance of the program already
        exists. It may be overwritten by subclasses.
        """
        import sys
        sys.exit(0)

if __name__ == '__main__':
    pass
