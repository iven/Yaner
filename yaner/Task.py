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

import glib
import os
from twisted.web import xmlrpc

from yaner.Constants import *
from yaner.Configuration import ConfigFile

# TODO: Error handle, metalink multiple gids

class Task:
    """
    General task class.
    """
    def __init__(self, main_app):
        # get server
        (server, server_model) = main_app.task_new_get_active_server()
        # get proxy
        server_proxy = server_model.proxy
        # get category
        cate_index = main_app.task_new_widgets['cate_cb'].get_active()
        cate = server_model.cates.keys()[cate_index]
        # task options
        options = dict(main_app.conf_file.default_conf)
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
        self.server_model = server_model
        self.server_proxy = server_proxy
        self.options = options
        self.info = {'server': server, 'cate': cate}
        self.conf_file = None
        self.iter = None

    def add_task(self, gid):
        """
        Add a new task when gid is received.
        An iter is added to queuing model and configuration
        file for this task is created.
        """
        print 'success #%s' % gid
        options = self.options
        self.info['gid'] = gid

        file_name = '%(server)s_%(cate)s_%(gid)s' % self.info
        conf = ConfigFile(os.path.join(U_TASK_CONFIG_DIR, file_name))
        conf['info'] = self.info
        conf['options'] = options

        queuing_model = self.server_model.iters.values()[ITER_QUEUING]
        self.main_app.tasklist_view.set_model(queuing_model)
        self.iter = queuing_model.append(None, [conf.info.gid,
            "gtk-new", self.task_name, 0, '', '', '', '', 1])

        glib.timeout_add_seconds(1, self.call_tell_status)
        self.conf_file = conf

    def call_tell_status(self):
        """
        Call server for the status of this task.
        Return True means keep calling it when timeout.
        """
        deferred = self.server_proxy.callRemote(
                "aria2.tellStatus", self.conf_file.info.gid)
        deferred.addCallback(self.update_iter)
        return True

    def update_iter(self, status):
        """
        Update data fields of the task iter.
        """
        if status['totalLength'] != '0':
            comp_length = status['completedLength']
            total_length = status['totalLength']
            percent = float(comp_length) / int(total_length) * 100
            self.server_model.iters.values()[ITER_QUEUING].set(self.iter,
                    3, percent, 4, '%.2f%%' % percent,
                    5, '%s / %s' % (comp_length, total_length),
                    6, status['downloadSpeed'], 7, status['uploadSpeed'],
                    8, int(status['connections']))

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
        deferred = self.server_proxy.callRemote(
                "aria2.addMetalink", m_binary, self.options)
        deferred.addCallback(self.add_task)

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
        if uris:
            self.info['uris'] = ','.join(uris)
            deferred = self.server_proxy.callRemote(
                    "aria2.addTorrent", t_binary, uris, self.options)
        else:
            deferred = self.server_proxy.callRemote(
                    "aria2.addTorrent", t_binary, self.options)
        deferred.addCallback(self.add_task)

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
            else:
                self.task_name = "New Normal Task"
        # Call server for new task
        deferred = self.server_proxy.callRemote(
                "aria2.addUri", uris, self.options)
        deferred.addCallback(self.add_task)

