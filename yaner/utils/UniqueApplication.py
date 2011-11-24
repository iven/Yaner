#!/usr/bin/env python
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
This module contains the super class of single instance applications
like L{yaner}.
"""

import dbus
import dbus.service
import dbus.mainloop.glib

class UniqueApplicationMixin(object):
    """
    This class uses DBus to ensure there is only one instance of
    this class.
    """

    def __init__(self, bus_name):
        """
        This firstly creates and binds a C{dbus.service.BusName}.
        When the second instances constructing, it fails and fallback
        to C{on_instance_exists}, which should be implemented in
        the subclass of L{UniqueApplicationMixin}.

        @arg bus_name:Unique name identifies the application. Such as
        'I{com.kissuki.yaner}'.
        @type bus_name:str
        """
        object.__init__(self)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default = True)
        self.bus = dbus.SessionBus()
        try:
            self.bus_name = dbus.service.BusName(bus_name,
                    self.bus, False, True, True)
        except dbus.exceptions.NameExistsException:
            self.on_instance_exists()

