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
This module contains the L{Pool} class of L{yaner}.
"""

import os

from gi.repository import GLib
from gi.repository import GObject
from sqlalchemy import Column, Unicode, Boolean
from sqlalchemy.orm import reconstructor, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from yaner.Xmlrpc import ServerProxy
from yaner.Database import SQLSession, SQLBase
from yaner.Presentable import Presentable, Queuing, Category, Dustbin
from yaner.utils.Logging import LoggingMixin

class Pool(SQLBase, GObject.GObject, LoggingMixin):
    """
    The Pool class of L{yaner}, which provides data for L{PoolModel}.

    A Pool is just a connection to the aria2 server, to avoid name conflict
    with download server.
    """

    __gsignals__ = {
            'connected': (GObject.SignalFlags.RUN_LAST, None, ()),
            'disconnected': (GObject.SignalFlags.RUN_LAST, None, ()),
            'presentable-added': (GObject.SignalFlags.RUN_LAST,
                None, (Presentable,)),
            'presentable-removed': (GObject.SignalFlags.RUN_LAST,
                None, (Presentable,)),
            }
    """
    GObject signals of this class.
    """

    _CONNECTION_INTERVAL = 5
    """Interval for keeping connection, in second(s)."""

    name = Column(Unicode)
    user = Column(Unicode)
    passwd = Column(Unicode)
    host = Column(Unicode)
    port = Column(Unicode)
    is_local = Column(Boolean)
    categories = relationship(Category, backref='pool',
                              cascade='all, delete-orphan')
    default_category = relationship(Category, uselist=False)

    def __init__(self, name, host, user='', passwd='', port='6800', is_local=False):
        self.name = name
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = port
        self.is_local = is_local

        SQLSession.add(self)
        SQLSession.commit()

        self._init()

    @reconstructor
    def _init(self):
        GObject.GObject.__init__(self)
        LoggingMixin.__init__(self)

        self._queuing = None
        self._categories = []
        self._dustbin = None

        self._connected = False
        self._proxy = None

        if self.default_category is None:
            self.logger.info('Creating default category for {}.'.format(self))
            down_dir = os.environ.get('XDG_DOWNLOAD_DIR', os.path.expanduser('~'))
            self.default_category = Category(name=_('My Downloads'),
                                             directory= down_dir,
                                             pool=self)
            SQLSession.commit()

        self.do_disconnected()
        self._keep_connection()

    def __repr__(self):
        return _("<Pool {}>").format(self.name)

    @property
    def proxy(self):
        """Get the xmlrpc proxy of the pool."""
        if self._proxy is None:
            connstr = 'http://{0.user}:{0.passwd}@{0.host}:{0.port}/rpc'
            self._proxy = ServerProxy(connstr.format(self))
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
        return [self.queuing] + self.categories + [self.dustbin]

    @hybrid_property
    def tasks(self):
        for category in self.categories:
            for task in category._tasks:
                yield task

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
        self.logger.info('{}: connected.'.format(self))
        self._resume_session()

    def do_disconnected(self):
        """When status changed, mark all queuing tasks as inactive.

        This will make a difference when start a task: paused tasks will
        call C{aria2.unpause} method, while inactive tasks will call
        C{aria2.addUri}, or other method to add them as new tasks.
        """
        self.logger.info('{}: disconnected.'.format(self))
        for task in self.queuing.tasks:
            task.state = 'inactive'

    def _keep_connection(self):
        """Keep calling C{aria2.getVersion} and mark pool as connected."""

        def on_got_version(deferred):
            """When got aria2 version, mark the pool as connected."""
            self.connected = True

        deferred = self.proxy.call('aria2.getVersion')
        deferred.add_callback(on_got_version)
        deferred.add_errback(self._on_xmlrpc_error)
        deferred.start()

        GLib.timeout_add_seconds(self._CONNECTION_INTERVAL,
                self._keep_connection)
        return False

    def _resume_session(self):
        """Get session id from pool."""

        def on_got_session_info(deferred):
            """When got session info, call L{yaner.Task.begin_update_status}
            on every task with the same session id.
            """
            session_info = deferred.result
            for task in self.queuing.tasks:
                if task.session_id == session_info['sessionId']:
                    task.state = 'waiting'
                    task.begin_update_status()

        deferred = self.proxy.call('aria2.getSessionInfo')
        deferred.add_callback(on_got_session_info)
        deferred.add_errback(self._on_xmlrpc_error)
        deferred.start()

    def _on_xmlrpc_error(self, deferred):
        """When we meet a xmlrpc error, it may be caused by network error,
        mark the server as disconnected.

        """
        self.connected = False

GObject.type_register(Pool)

