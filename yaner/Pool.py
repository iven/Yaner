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
            'disconnected': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ()),
            'presentable-added': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Presentable,)),
            'presentable-removed': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Presentable,)),
            'presentable-changed': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Presentable,)),
            }
    """
    GObject signals of this class.
    """

    _SESSION_CHECK_INTERVAL = 20
    """Interval for checking if it's a new session, in second(s)."""

    name = sqlobject.UnicodeCol()
    user = sqlobject.StringCol(default='')
    passwd = sqlobject.StringCol(default='')
    host = sqlobject.StringCol()
    port = sqlobject.IntCol(default=6800)
    session_id = sqlobject.StringCol(default='')

    categories = sqlobject.MultipleJoin('Category')
    tasks = sqlobject.MultipleJoin('Task')

    def _init(self, *args, **kwargs):
        LoggingMixin.__init__(self)
        gobject.GObject.__init__(self)
        sqlobject.SQLObject._init(self, *args, **kwargs)

        self._queuing = None
        self._categories = []
        self._dustbin = None

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
        return [self.queuing] + self.categories + [self.dustbin]

    def queuing_changed(self, queuing):
        """
        If the name of queuing presentable changed, update the config.
        """
        if queuing.name != self.config['info']['name']:
            self.config['info']['name'] = queuing.name

    def _check_session_info(self):
        """Check if it is a new aria2 session, by get session info from aria2
        server. A new session means either it's first start of L{yaner}, or
        the aria2 server is restarted, so we should call L{_got_session_info}
        to do some work.

        This also checks if the server is working well.

        """
        deferred = self.proxy.callRemote('aria2.getSessionInfo')
        deferred.addCallbacks(self._on_got_session_info, self._on_twisted_error)
        glib.timeout_add_seconds(self._SESSION_CHECK_INTERVAL,
                self._check_session_info)
        return False

    def _on_got_session_info(self, session_info):
        """When got session info, compare it with the saved session id.
        If it's a new session, we should add tasks which need to be started
        to the server.

        Also we should mark the server as connected.

        """
        pass

    def _on_twisted_error(self, failure):
        """When we meet a twisted error, it may be caused by network error,
        mark the server as disconnected.

        """
        pass

