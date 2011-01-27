#!/usr/bin/env python2
# vim:fileencoding=UTF-8

# This file is part of Yaner.

# Yaner - GTK+ interface for aria2 download mananger
# Copyright (C) 2010-2011  Iven <ivenvd#gmail.com>
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
This module contains the main application class of L{yaner}.
"""

from twisted.internet import reactor

from ui.Toplevel import Toplevel
from utils.UniqueApplication import UniqueApplication

class Application(UniqueApplication):
    """Main application of L{yaner}."""

    BUS_NAME = 'com.kissuki.yaner'
    """
    The unique bus name of the application, which identifies the
    application when using DBus to implement the L{UniqueApplication}
    class.
    """

    def __init__(self):
        """
        The init methed of L{Application} class.

        It handles command line options, creates L{toplevel window
        <Toplevel>}, and implements L{UniqueApplication} interface.
        """
        UniqueApplication.__init__(self, BUS_NAME)
        self._toplevel = Toplevel()
        self._toplevel.show()
        self._toplevel.connect("destroy", self.on_toplevel_destroy)

    @property
    def toplevel(self):
        """Get the toplevel window of L{yaner}."""
        return self._toplevel

    @staticmethod
    def on_toplevel_destroy(data):
        """
        The callback function of the I{destory} signal of L{toplevel}.
        @arg data:B{NOT} used.
        """
        reactor.stop()

    def run(self):
        """Run the main loop of the application."""
        reactor.run()

