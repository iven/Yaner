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
This module contains the L{Pool} class of L{yaner}.
"""

import glib
import gobject
import sqlobject

from twisted.web import xmlrpc

from yaner.Task import Task
from yaner.Misc import GObjectSQLObjectMeta
from yaner.Presentable import Presentable, Queuing, Dustbin
from yaner.utils.Logging import LoggingMixin
from yaner.utils.Notification import Notification

class Pool(sqlobject.SQLObject, gobject.GObject, LoggingMixin):
    """
    The Pool class of L{yaner}, which provides data for L{PoolModel}.

    A Pool is just a connection to the aria2 server, to avoid name conflict
    with download server.
    """

    __metaclass__ = GObjectSQLObjectMeta

    __gsignals__ = {
            'connected': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ()),
            'disconnected': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ()),
            'presentable-added': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Presentable,)),
            'presentable-removed': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Presentable,)),
            }
    """
    GObject signals of this class.
    """

    _CONNECTION_INTERVAL = 5
    """Interval for keeping connection, in second(s)."""

    name = sqlobject.UnicodeCol()
    user = sqlobject.StringCol(default='')
    passwd = sqlobject.StringCol(default='')
    host = sqlobject.StringCol()
    port = sqlobject.IntCol(default=6800)

    categories = sqlobject.SQLMultipleJoin('Category')
    tasks = sqlobject.SQLMultipleJoin('Task')

    def _init(self, *args, **kwargs):
        LoggingMixin.__init__(self)
        gobject.GObject.__init__(self)
        sqlobject.SQLObject._init(self, *args, **kwargs)

        self._queuing = None
        self._categories = []
        self._dustbin = None

        self._connected = False
        self._proxy = None

        self.do_disconnected()
        self._keep_connection()

    @property
    def proxy(self):
        """Get the xmlrpc proxy of the pool."""
        if self._proxy is None:
            connstr = 'http://{0.user}:{0.passwd}@{0.host}:{0.port}/rpc'
            self._proxy = xmlrpc.Proxy(connstr.format(self))
        return self._proxy

    @property
    def queuing(self):
        """Get the queuing presentable of the pool."""
        if self._queuing is None:
            self._queuing = Queuing(self)
        return self._queuing

    @property
    def dustbin(self):
        """Get the dustbin presentable of the pool."""
        if self._dustbin is None:
            self._dustbin = Dustbin(self)
        return self._dustbin

    @property
    def presentables(self):
        """Get the presentables of the pool."""
        return [self.queuing] + list(self.categories) + [self.dustbin]

    @property
    def connected(self):
        """Get the connection status of the pool."""
        return self._connected

    @connected.setter
    def connected(self, new_status):
        if new_status != self.connected:
            self._connected = new_status
            if self._connected:
                self.emit('connected')
            else:
                self.emit('disconnected')
            self.queuing.emit('changed')

    def do_connected(self):
        """When pool connected, try to resume last session."""
        self._resume_session()

    def do_disconnected(self):
        """When status changed, mark all queuing tasks as inactive.

        This will make a difference when start a task: paused tasks will
        call C{aria2.unpause} method, while inactive tasks will call
        C{aria2.addUri}, or other method to add them as new tasks.
        """
        for task in self.queuing.tasks:
            task.status = Task.STATUSES.INACTIVE
            task.end_update_status()
            task.changed()

    def _keep_connection(self):
        """Keep calling C{aria2.getVersion} and mark pool as connected."""

        def on_got_version(version):
            """When got aria2 version, mark the pool as connected."""
            self.connected = True

        deferred = self.proxy.callRemote('aria2.getVersion')
        deferred.addCallbacks(on_got_version, self._on_twisted_error)

        glib.timeout_add_seconds(self._CONNECTION_INTERVAL,
                self._keep_connection)
        return False

    def _resume_session(self):
        """Get session id from pool."""

        def on_got_session_info(session_info):
            """When got session info, call L{yaner.Task.begin_update_status}
            on every task with the same session id.
            """
            for task in self.queuing.tasks.filter(
                    Task.q.session_id == session_info['sessionId']):
                task.status = Task.STATUSES.ACTIVE
                task.begin_update_status()

        deferred = self.proxy.callRemote('aria2.getSessionInfo')
        deferred.addCallbacks(on_got_session_info, self._on_twisted_error)

    def _on_twisted_error(self, failure):
        """When we meet a twisted error, it may be caused by network error,
        mark the server as disconnected.

        """
        self.connected = False

