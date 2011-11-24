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

"""This module contains async xmlrpc proxy."""

import socket
import httplib
import xmlrpclib
import threading

from functools import partial
from gi.repository import GLib
from gi.repository import GObject

class _Deferred(threading.Thread, GObject.GObject):

    __gsignals__ = {
            'success': (GObject.SignalFlags.RUN_LAST, None, ()),
            'fault': (GObject.SignalFlags.RUN_LAST, None, ()),
            'error': (GObject.SignalFlags.RUN_LAST, None, ()),
            }

    def __init__(self, target, args=(), kwargs=None):
        threading.Thread.__init__(self)
        GObject.GObject.__init__(self)

        self.target = target
        self.args = args
        self.kwargs = kwargs if kwargs else {}

        self.result = None
        self.fault = None
        self.error = None

    def add_callback(self, func):
        """Connect signal "success" to func."""
        self.connect("success", partial(GLib.idle_add, func))
        return self

    def add_errback(self, func):
        """Connect signal "error" to func."""
        self.connect("error", partial(GLib.idle_add, func))
        return self

    def add_faultback(self, func):
        """Connect signal "fault" to func."""
        self.connect("fault", partial(GLib.idle_add, func))
        return self

    def run(self):
        """The actual function of the call.

        If the call returned successfully, L{self.result} will be set and
        the "success" signal emits. If the call throws a Fault, L{self.fault}
        will be set and the "fault" signal emits. If the call throws other
        exceptions, L{self.error} will be set and the "error" signal emits.
        """
        try:
            self.result = self.target(*self.args, **self.kwargs)
        except xmlrpclib.Fault as self.fault:
            self.emit('fault')
        except socket.error as self.error:
            self.emit('error')
        except httplib.error as self.error:
            self.emit('error')
        except xmlrpclib.ProtocolError as self.error:
            self.emit('error')
        else:
            self.emit('success')

class ServerProxy(object):
    """Designed to replace ServerProxy class in the standard library,
    which is not threadsafe. This class create a std C{ServerProxy}
    when making a remote call.
    """

    def __init__(self, connstr):
        """L{ServerProxy} initializing.

        @arg connstr:The connection string of the proxy.
        @type connstr:L{str}

        """
        self.connstr = connstr

    def call(self, funcstr, *args, **kwargs):
        """Create a std C{ServerProxy} and return a L{_Deferred} to
        call it. The returned L{_Deferred} must be started manually.
        """
        proxy = xmlrpclib.ServerProxy(self.connstr)
        func = getattr(proxy, funcstr)
        return _Deferred(func, args=args, kwargs=kwargs)

