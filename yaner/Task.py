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

#import gtk
import glib
import os

from yaner.Constants import TASK_NORMAL, TASK_BT, TASK_METALINK
from yaner.Constants import U_TASK_CONFIG_DIR
from yaner.Configuration import ConfigFile

# TODO: Error Handle

class Task:
    def __init__(self, main_app, task_type, server, cate, params):
        server_model = main_app.server_view.servers[server]
        proxy = server_model.proxy
        task_iter = server_model.cates[cate]
        model = server_model.iters[task_iter]
        main_app.tasklist_view.set_model(model)
        method = ("Uri", "Torrent", "Metalink")[task_type]
        deferred = proxy.callRemote("aria2.add" + method, params[0], params[1])
        deferred.addCallback(self.add_task, task_type, server, cate, params)
        self.main_app = main_app
        self.server_model = server_model
        self.proxy = proxy
        self.model = model

    def add_task(self, gid, task_type, server, cate, params):
        print 'success'
        self.gid = gid
        file_name = '_'.join((server, cate, gid))
        conf = ConfigFile(os.path.join(U_TASK_CONFIG_DIR, file_name))
        # get URIs
        if task_type == TASK_NORMAL:
            conf.info['uris'] = ','.join(params[0])
        elif task_type == TASK_BT:
            conf.info['torrent'] = params[0]
            if len(params) > 2:
                conf.info['uris'] = ','.join(params[1])
        elif task_type == TASK_METALINK:
            conf.info['metalink'] = params[0]
        # other options
        conf.info['server'] = server
        conf.info['cate'] = cate
        conf.info['type'] = task_type
        conf['options'] = params[-1]
        self.conf = conf
        deferred = self.proxy.callRemote("aria2.tellStatus", gid)
        deferred.addCallback(self.add_iter, conf.options)

    def add_iter(self, status, options):
        self.iter = self.model.append(None, [
            status['gid'], status['status'], options['out'], 
            options['dir'], status['totalLength'],
            status['downloadSpeed'], status['uploadSpeed'],
            int(status['connections'])])

        glib.timeout_add_seconds(1, self.call_tell_status)

    def call_tell_status(self):
        deferred = self.proxy.callRemote("aria2.tellStatus", self.gid)
        deferred.addCallback(self.update_iter)
        return True

    def update_iter(self, status):
        options = self.conf.options
        self.model.set(self.iter, 0, status['gid'],
                1, status['status'], 2, options['out'], 
                3, options['dir'], 4, status['totalLength'],
                5, status['downloadSpeed'], 6, status['uploadSpeed'],
                7, int(status['connections']))

        self.status = status

