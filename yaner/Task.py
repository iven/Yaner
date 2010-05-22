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

class Task:
    """
    General task class.
    """
    def __init__(self, main_app):
        # get server
        index = main_app.task_new_widgets['server_cb'].get_active()
        (server_name, server) = main_app.server_group.servers.items()[index]
        # get category
        cate_index = main_app.task_new_widgets['cate_cb'].get_active()
        cate_name = server.cates[cate_index]
        # task options
        options = dict(main_app.conf.default)
        for (pref, widget) in main_app.task_new_prefs.iteritems():
            if pref == 'seed-ratio':
                options[pref] = str(widget.get_value())
            elif hasattr(widget, 'get_value'):
                options[pref] = str(int(widget.get_value()))
            elif hasattr(widget, 'get_text'):
                options[pref] = widget.get_text()
        # clear empty items
        for (pref, value) in options.items():
            if not value:
                del options[pref]
        # bt prioritize
        if main_app.task_new_prefs['bt-prioritize-piece'].get_active():
            options['bt-prioritize-piece'] = 'head,tail'

        self.main_app = main_app
        self.server = server
        self.options = options
        self.info = {'server': server_name, 'cate': cate_name}
        self.conf = None
        self.iter = None
        self.healthy = False

    def add_task(self, gid):
        """
        Add a new task when gid is received.
        An iter is added to queuing model and configuration
        file for this task is created.
        """
        # Workaround for Metalink. TODO: Fix this workaround.
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
            self.server.models[ITER_QUEUING].set(
                    self.iter, 3, 100, 4, '100%')
            self.healthy = False
        elif not 'totalLength' in status:
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

class MetalinkTask(Task):
    """
    Metalink Task Class
    """
    def __init__(self, main_app, metalink):
        Task.__init__(self, main_app)
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

class BTTask(Task):
    """
    BT Task Class
    """
    def __init__(self, main_app, torrent, uris):
        Task.__init__(self, main_app)
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

class NormalTask(Task):
    """
    Normal Task Class
    """
    def __init__(self, main_app, uris):
        Task.__init__(self, main_app)
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

