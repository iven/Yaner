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
from twisted.web import xmlrpc

from yaner.Constants import *
from yaner.Constants import _
from yaner.Configuration import ConfigFile
from yaner.ODict import ODict

class ServerModel:
    """
    Aria2 server tree model of the left pane in the main window.
    This contains queuing, completed, recycled tasks as its children.
    """

    def __init__(self, treeview, treestore, server_conf, server_cates):
        # Preferences
        self.conf = server_conf
        self.connected = False
        self.proxy = xmlrpc.Proxy(self.__get_conn_str())
        # Iters
        server_iter = treestore.append(None,
                ["gtk-disconnect", self.conf.name])
        queuing_iter = treestore.append(server_iter,
                ["gtk-media-play", _("Queuing")])
        completed_iter = treestore.append(server_iter,
                ["gtk-apply", _("Completed")])
        recycled_iter = treestore.append(server_iter,
                ["gtk-cancel", _("Recycled")])
        # Category Iters
        cates = ODict()
        for cate_name in server_cates:
            cate_iter = treestore.append(completed_iter,
                    ["gtk-directory", cate_name[5:]])
            cates[cate_name] = cate_iter
        # Setup task list model for each iter
        iter_list = [server_iter, queuing_iter, completed_iter, recycled_iter]
        iter_list.extend(cates.values())
        iters = ODict()
        for key in iter_list:
            iters[key] = gtk.TreeStore(
                    gobject.TYPE_STRING, # gid
                    gobject.TYPE_STRING, # status
                    gobject.TYPE_STRING, # name
                    gobject.TYPE_FLOAT,  # progress value
                    gobject.TYPE_STRING, # progress text
                    gobject.TYPE_STRING, # size
                    gobject.TYPE_STRING, # download speed
                    gobject.TYPE_STRING, # upload speed
                    gobject.TYPE_INT     # connections
                    )
        self.treeview = treeview
        self.treestore = treestore
        self.cates = cates
        self.iters = iters

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
        self.treestore.set(self.iters.keys()[ITER_SERVER], 0,
                'gtk-connect' if connected else 'gtk-disconnect')

class ServerView:
    """
    Aria2 server treeview in the left pane.
    """
    def __init__(self, main_app, treeview, treestore):
        # TreeSelection
        selection = treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect("changed", self.on_selection_changed)
        # TreeModel
        servers = ODict()
        server_conf_file = ConfigFile(U_SERVER_CONFIG_FILE)
        for server in main_app.conf_file.main.servers.split(','):
            server_conf = server_conf_file[server]
            server_cates = main_app.conf_file.cate[server].split(',')
            server_model = ServerModel(self, treestore, 
                    server_conf, server_cates)
            servers[server] = server_model

        self.main_app = main_app
        self.treeview = treeview
        self.treestore = treestore
        self.selection = selection
        self.servers = servers

    def on_selection_changed(self, selection, data = None):
        """
        TreeView selection changed callback, changing the model of
        TaskView according to the selected row.
        """
        (treemodel, treeiter) = selection.get_selected()

