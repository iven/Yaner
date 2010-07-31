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
    This file contains classes about aria2 servers.
"""

import gtk
import gobject
import os
import uuid
from twisted.web import xmlrpc

from yaner.Constants import U_SERVER_CONFIG_FILE, U_TASK_CONFIG_DIR
from yaner.Constants import ITER_COMPLETED, ITER_SERVER, ITER_COUNT
from yaner.Constants import _
from yaner.Configuration import ConfigFile
from yaner.ODict import ODict
from yaner.Task import TASK_CLASSES

class Server:
    """
    Tree model for each aria2 server of the left pane in the main window.
    This contains queuing, completed, recycled tasks as its children.
    'group': the ServerGroup which the Server is in.
    'conf': the server ConfigFile.
    'cates': the categories list of the server.
    'iters': iters list.
    'model': tasklist models of each iter.
    'proxy': xmlrpc server proxy.
    'connected: a boolean if the xmlrpc server is connected.
    """

    def __init__(self, group, conf):
        model = group.view.get_model()
        # Preferences
        self.group = group
        self.conf = conf
        self.connected = False
        self.proxy = xmlrpc.Proxy(self.__get_conn_str())
        # Categories
        self.cates = conf.cates.split(',')
        # Iters
        server_iter = model.append(None, ["gtk-disconnect", conf.name])
        self.iters = [
                server_iter,
                model.append(server_iter, ["gtk-media-play", _("Queuing")]),
                model.append(server_iter, ["gtk-apply", _("Completed")]),
                model.append(server_iter, ["gtk-cancel", _("Recycled")]),
                ]
        for cate_name in self.cates:
            cate_iter = model.append(self.iters[ITER_COMPLETED],
                    ["gtk-directory", cate_name[5:]])
            self.iters.append(cate_iter)
        # Models
        self.models = []
        for i in xrange(len(self.iters)):
            self.models.append(gtk.TreeStore(
                    gobject.TYPE_STRING, # gid
                    gobject.TYPE_STRING, # status
                    gobject.TYPE_STRING, # name
                    gobject.TYPE_FLOAT,  # progress value
                    gobject.TYPE_STRING, # progress text
                    gobject.TYPE_STRING, # size
                    gobject.TYPE_STRING, # download speed
                    gobject.TYPE_STRING, # upload speed
                    gobject.TYPE_INT     # connections
                    ))

    def __get_conn_str(self):
        """
        Generate a connection string used by xmlrpc.
        """
        return 'http://%(user)s:%(passwd)s@%(host)s:%(port)s/rpc' % self.conf

    def set_connected(self, connected):
        """
        Set if client is connected to the server.
        """
        self.connected = connected
        self.group.model.set(self.iters[ITER_SERVER], 0,
                'gtk-connect' if connected else 'gtk-disconnect')

    def add_task(self, info = None, options = None, conf = None, is_new = True):
        """
        Add task to server, from info + options, or conf.
        If a task is new added to the server, is_new should be True.
        if we just want to display an existing task on the server, is_new will be False.
        """
        if conf == None:
            # Must be new task, generate a conf file for it.
            file_name = str(uuid.uuid1())
            conf = ConfigFile(os.path.join(U_TASK_CONFIG_DIR, file_name))
            conf['info'] = info
            conf['options'] = options

        TASK_CLASSES[int(conf.info.type)](self, conf, is_new)

class ServerGroup:
    """
    Aria2 server group in the treeview of the left pane.
    """
    def __init__(self, main_app, view):
        self.main_app = main_app
        self.view = view
        self.servers = ODict()
        # TreeModel
        self.conf = ConfigFile(U_SERVER_CONFIG_FILE)
        for server in main_app.conf.main.servers.split(','):
            self.servers[server] = Server(self, self.conf[server])
        # TreeSelection
        selection = view.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect("changed", self.on_selection_changed)

    def on_selection_changed(self, selection):
        """
        TreeView selection changed callback, changing the model of
        TaskView according to the selected row.
        """
        (model, selected_iter) = selection.get_selected()
        path = model.get_path(selected_iter)
        # if not the server iter
        if len(path) > 1:
            model_index = path[-1] + (1, ITER_COUNT)[len(path) - 2]
            server = self.servers.values()[path[0]]
            tasklist_model = server.models[model_index]
            self.main_app.tasklist_view.set_model(tasklist_model)

