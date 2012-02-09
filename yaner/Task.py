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
This module contains the L{Task} class of L{yaner}.
"""

import os

from gi.repository import GLib
from gi.repository import GObject
from sqlalchemy import Column, Integer, PickleType, Unicode, ForeignKey
from sqlalchemy.orm import reconstructor, deferred
from sqlalchemy.ext.hybrid import hybrid_property

from yaner import SQLBase, SQLSession
from yaner.Misc import unquote
from yaner.utils.Logging import LoggingMixin
from yaner.utils.MutationDict import MutationDict
from yaner.utils.Notification import Notification

class Task(SQLBase, GObject.GObject, LoggingMixin):
    """
    Task class is just downloading tasks, which provides data to L{TaskListModel}.
    """

    __gsignals__ = {
            'changed': (GObject.SignalFlags.RUN_LAST, None, ()),
            }
    """GObject signals of this class."""

    _UPDATE_INTERVAL = 1
    """Interval for status updating, in second(s)."""

    _SYNC_INTERVAL = 60
    """Interval for database sync, in second(s)."""

    name = Column(Unicode)
    status = Column(MutationDict.as_mutable(PickleType))

    uris = Column(PickleType, default=[])
    torrent = deferred(Column(PickleType, default=None))
    metafile = deferred(Column(PickleType, default=None))

    options = Column(MutationDict.as_mutable(PickleType))
    session_id = Column(Unicode, default='')
    category_id = Column(Integer, ForeignKey('category.id'))

    def __init__(self, name, category, options, uris=[],
                 torrent=None, metafile=None):
        self.name = name
        self.status = {
            'completedLength': '0',
            'totalLength': '0',
            'downloadSpeed': '0',
            'uploadSpeed': '0',
            'connections': '0',
            'gid': '',
            'status': 'inactive',
        }

        self.uris = uris
        self.torrent = torrent
        self.metafile = metafile

        self.options = options
        self.category = category

        LoggingMixin.__init__(self)
        self.logger.info(_('Adding new task: {}...').format(self))
        self.logger.debug(_('Task options: {}').format(options))

        SQLSession.add(self)
        SQLSession.commit()

        self._init()

    @reconstructor
    def _init(self):
        LoggingMixin.__init__(self)
        GObject.GObject.__init__(self)

        self._status_update_handle = None
        self._database_sync_handle = None

        self._name_fixed = False

    def __repr__(self):
        return _("<Task {}>").format(self.name)

    @hybrid_property
    def pool(self):
        return self.category.pool

    @hybrid_property
    def state(self):
        """Download status of the task, must be one of: 'inactive', 'active',
        'paused', 'waiting', 'complete', 'removed', 'error'.
        """
        return self.status['status']

    @state.setter
    def state(self, state):
        """Always sync when task state changes."""
        if hash(self) and self.state != state:
            self.status['status'] = state
            SQLSession.commit()
            self.emit('changed')
        else:
            self.status['status'] = state

    @hybrid_property
    def in_queuing(self):
        return self.state not in ['complete', 'removed']

    @hybrid_property
    def in_category(self):
        return self.state == 'complete'

    @hybrid_property
    def in_dustbin(self):
        return self.state == 'removed'

    @property
    def gid(self):
        return self.status['gid']

    @gid.setter
    def gid(self, gid):
        self.status['gid'] = gid

    @property
    def total_length(self):
        return int(self.status['totalLength'])

    @property
    def completed_length(self):
        return int(self.status['completedLength'])

    @property
    def download_speed(self):
        return int(self.status['downloadSpeed'])

    @property
    def upload_speed(self):
        return int(self.status['uploadSpeed'])

    @property
    def connections(self):
        return int(self.status['connections'])

    @property
    def has_bittorrent(self):
        """Check if task use bittorrent protocol."""
        return 'bittorrent' in self.status

    @property
    def is_completed(self):
        """Check if task is completed, useful for task undelete."""
        return (self.state == 'complete') or \
                (self.total_length and (self.total_length == self.completed_length))

    @property
    def is_active(self):
        """Check if task is active."""
        return self.state == 'active'

    @property
    def is_running(self):
        """Check if task is running."""
        return self.state in ['active', 'waiting', 'paused']

    @property
    def is_trashed(self):
        """Check if task is removable."""
        return self.state == 'removed'

    @property
    def is_addable(self):
        """Check if task is addable."""
        return self.state in ['inactive', 'error']

    @property
    def is_pausable(self):
        """Check if task is pausable."""
        return self.state in ['active', 'waiting']

    @property
    def is_unpausable(self):
        """Check if task is unpausable."""
        return self.state == 'paused'

    def add(self):
        """Add the task to pool."""
        proxy = self.pool.proxy
        options = dict(self.options)
        if self.metafile:
            deferred = proxy.call('aria2.addMetalink', self.metafile, options)
        elif self.torrent:
            deferred = proxy.call('aria2.addTorrent', self.torrent,
                                  self.uris, options)
        else:
            deferred = proxy.call('aria2.addUri', self.uris, options)

        deferred.add_callback(self._on_started)
        deferred.add_errback(self._on_xmlrpc_error)
        deferred.start()

    def start(self):
        """Unpause task if it's paused, otherwise add it (again)."""
        if self.is_unpausable:
            deferred = self.pool.proxy.call('aria2.unpause', self.gid)
            deferred.add_callback(self._on_unpaused)
            deferred.add_errback(self._on_xmlrpc_error)
            deferred.start()
        elif self.is_addable:
            self.add()
            self.pool.queuing.add_task(self)

    def pause(self):
        """Pause task if it's running."""
        if self.is_pausable:
            deferred = self.pool.proxy.call('aria2.pause', self.gid)
            deferred.add_callback(self._on_paused)
            deferred.add_errback(self._on_xmlrpc_error)
            deferred.start()

    def trash(self):
        """Move task to dustbin."""
        if not self.is_trashed:
            if self.is_running:
                deferred = self.pool.proxy.call('aria2.remove', self.gid)
                deferred.add_callback(self._on_trashed)
                deferred.add_errback(self._on_xmlrpc_error)
                deferred.start()
            else:
                self._on_trashed()

    def restore(self):
        """Restore task."""
        if self.is_trashed:
            self.pool.dustbin.remove_task(self)
            if self.is_completed:
                self.category.add_task(self)
                self.state = 'complete'
            else:
                self.pool.queuing.add_task(self)
                self.state = 'inactive'

    def remove(self):
        """Remove task."""
        if self.is_trashed:
            self.pool.dustbin.remove_task(self)
            SQLSession.delete(self)
            SQLSession.commit()

    def begin_update_status(self):
        """Begin to update status every second. Task must be marked
        waiting before calling this.
        """
        if self._status_update_handle is None:
            self.logger.info(_('{}: begin updating status.').format(self))
            self._status_update_handle = GLib.timeout_add_seconds(
                    self._UPDATE_INTERVAL, self._call_tell_status)
            self._database_sync_handle = GLib.timeout_add_seconds(
                    self._SYNC_INTERVAL, SQLSession.commit)

    def end_update_status(self):
        """Stop updating status every second."""
        if self._status_update_handle:
            self.logger.info(_('{}: end updating status.').format(self))
            GLib.source_remove(self._status_update_handle)
            self._status_update_handle = None
        if self._database_sync_handle:
            GLib.source_remove(self._database_sync_handle)
            self._database_sync_handle = None

    def _update_session_id(self):
        """Get session id of the pool and store it in task."""
        def on_got_session_info(deferred):
            """Set session id the task belongs to."""
            self.session_id = deferred.result['sessionId']
            SQLSession.commit()

        deferred = self.pool.proxy.call('aria2.getSessionInfo', self.gid)
        deferred.add_callback(on_got_session_info)
        deferred.add_errback(self._on_xmlrpc_error)
        deferred.start()

    def _on_started(self, deferred):
        """Task started callback, update task information."""

        gid = deferred.result
        self.gid = gid[-1] if isinstance(gid, list) else gid
        self.state = 'active'

        self._update_session_id()
        self.begin_update_status()

    def _on_paused(self, deferred):
        """Task paused callback, update state."""
        self.state = 'paused'

    def _on_unpaused(self, deferred):
        """Task unpaused callback, update state."""
        self.state = 'active'

    def _on_trashed(self, deferred=None):
        """Task removed callback, remove task from previous presentable and
        move it to dustbin.
        """
        in_category = self.in_category
        self.state = 'removed'
        if in_category:
            self.category.remove_task(self)
        else:
            self.pool.queuing.remove_task(self)
        self.pool.dustbin.add_task(self)

    def _call_tell_status(self):
        """Call pool for the status of this task.

        Return True to keep calling this when timeout else stop.

        """
        if self.is_running:
            deferred = self.pool.proxy.call('aria2.tellStatus', self.gid)
            deferred.add_callback(self._update_status)
            deferred.add_errback(self._on_xmlrpc_error)
            deferred.start()
            return True
        else:
            self.end_update_status()
            return False

    def _update_status(self, deferred):
        """Update data fields of the task."""
        status = deferred.result

        # Choose the best task name
        if not self._name_fixed:
            if self.has_bittorrent:
                name = unquote(status['bittorrent']['info']['name'])
                if name != '':
                    self.name = name
                    self._name_fixed = True
            else:
                files = status['files']
                if len(files) == 1:
                    name = unquote(os.path.basename(files[0]['path']))
                    if name != '':
                        self.name = name
                        self._name_fixed = True

        # If state changed, set task changed and commit to database
        self.state = status['status']
        self.status = status

        if self.is_completed:
            self.pool.queuing.remove_task(self)
            self.category.add_task(self)
        elif self.is_trashed:
            # Necessary?
            return self._on_trashed()
        else:
            self.emit('changed')

        self.pool.connected = True

    def _on_xmlrpc_error(self, deferred):
        """Handle errors occured when calling some function via xmlrpc."""
        self.state = 'error'
        message = getattr(deferred.error, 'message', str(deferred.error))
        Notification(_('Network Error'), message).show()

GObject.type_register(Task)

