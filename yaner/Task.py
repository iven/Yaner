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
    This file contains classes about download tasks.
"""

from __future__ import division
import gtk
import glib
import os
import xmlrpclib
from twisted.web import xmlrpc
from twisted.internet.error import ConnectionRefusedError

from yaner.Constants import *
from yaner.Pretty import psize, pspeed
from yaner.Configuration import ConfigFile

class TaskMixin:
    """
    General task class.
    """
    def __init__(self, main_app, info, options):
        self.main_app = main_app
        self.server = main_app.server_group.servers[info['server']]
        self.options = options
        self.info = info
        self.conf = None
        self.iter = None
        self.healthy = False

    def add_task(self, gid):
        """
        Add a new task when gid is received.
        An iter is added to queuing model and configuration
        file for this task is created.
        """
        # FIXME: Workaround for Metalink.
        self.info['gid'] = gid[-1] if type(gid) is list else gid

        file_name = '%(server)s_%(cate)s_%(gid)s' % self.info
        conf = ConfigFile(os.path.join(U_TASK_CONFIG_DIR, file_name))
        conf['info'] = self.info
        conf['options'] = self.options

        queuing_model = self.server.models[ITER_QUEUING]
        self.main_app.tasklist_view.set_model(queuing_model)
        self.iter = queuing_model.append(None, [conf.info.gid,
            "gtk-new", self.task_name, 0, '', '', '', '', 1])

        glib.timeout_add_seconds(1, self.call_tell_status)
        self.conf = conf
        self.healthy = True

    def add_task_error(self, failure):
        """
        Handle errors occured when calling add_task.
        """
        failure.check(ConnectionRefusedError, xmlrpclib.Fault)
        dialog = gtk.MessageDialog(self.main_app.main_window,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                failure.getErrorMessage())
        dialog.run()
        dialog.destroy()
        return failure

    def call_tell_status(self):
        """
        Call server for the status of this task.
        Return True means keep calling it when timeout.
        """
        deferred = self.server.proxy.callRemote(
                "aria2.tellStatus", self.conf.info.gid)
        deferred.addCallbacks(self.update_iter, self.update_iter_error)
        return self.healthy

    def update_iter(self, status):
        """
        Update data fields of the task iter.
        """
        if status['status'] == 'complete':
            self.healthy = False
        if not 'totalLength' in status:
            print status
        else:
            comp_length = status['completedLength']
            total_length = status['totalLength']
            percent = int(comp_length) / int(total_length) * 100 \
                    if total_length != '0' else 0
            self.server.models[ITER_QUEUING].set(self.iter,
                    3, percent,
                    4, '%.2f%% / %s' % (percent, psize(comp_length)),
                    5, psize(total_length),
                    6, pspeed(status['downloadSpeed']),
                    7, pspeed(status['uploadSpeed']),
                    8, int(status['connections']))

    def update_iter_error(self, failure):
        """
        Handle errors occured when calling update_iter.
        """
        failure.check(ConnectionRefusedError, xmlrpclib.Fault)
        if self.healthy:
            self.healthy = False
            dialog = gtk.MessageDialog(self.main_app.main_window,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                    failure.getErrorMessage())
            dialog.run()
            dialog.destroy()
        return failure

class MetalinkTask(TaskMixin):
    """
    Metalink Task Class
    """
    def __init__(self, main_app, metalink, info, options):
        TaskMixin.__init__(self, main_app, info, options)
        self.info['type'] = TASK_METALINK
        self.info['metalink'] = metalink
        # Task name
        self.task_name = 'New Metalink Task'
        # Encode file
        with open(metalink) as m_file:
            m_binary = xmlrpc.Binary(m_file.read())
        # Call server for new task
        deferred = self.server.proxy.callRemote(
                "aria2.addMetalink", m_binary, self.options)
        deferred.addCallbacks(self.add_task, self.add_task_error)

class BTTask(TaskMixin):
    """
    BT Task Class
    """
    def __init__(self, main_app, torrent, uris, info, options):
        TaskMixin.__init__(self, main_app, info, options)
        self.info['type'] = TASK_BT
        self.info['torrent'] = torrent
        # Task name
        self.task_name = 'New BT Task'
        # Encode file
        with open(torrent) as t_file:
            t_binary = xmlrpc.Binary(t_file.read())
        # Call server for new task
        self.info['uris'] = ','.join(uris)
        deferred = self.server.proxy.callRemote(
                "aria2.addTorrent", t_binary, uris, self.options)
        deferred.addCallbacks(self.add_task, self.add_task_error)

class NormalTask(TaskMixin):
    """
    Normal Task Class
    """
    def __init__(self, main_app, uris, info, options):
        TaskMixin.__init__(self, main_app, info, options)
        self.info['type'] = TASK_NORMAL
        self.info['uris'] = ','.join(uris)
        # Task name
        if 'out' in self.options:
            self.task_name = self.options['out']
        else:
            for uri in uris:
                if '/' in uri:
                    self.task_name = uri.split('/')[-1]
                    break
            else:
                self.task_name = "New Normal Task"
        # Call server for new task
        deferred = self.server.proxy.callRemote(
                "aria2.addUri", uris, self.options)
        deferred.addCallbacks(self.add_task, self.add_task_error)

