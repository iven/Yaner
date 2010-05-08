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
from twisted.web import xmlrpc

from yaner.Constants import U_SERVER_CONFIG_FILE, _
from yaner.Configuration import ConfigFile

class ServerModel:
    """
    Aria2 server tree model of the left pane in the main window.
    This contains queuing, completed, recycled tasks as its children.
    """

    def __init__(self, treeview, treestore, server_conf, server_cates):
        # Preferences
        self.conf = server_conf
        self.cates = server_cates
        self.connected = False
        self.proxy = xmlrpc.Proxy(self.__get_conn_str())
        # Iters
        self.server_iter = treestore.append(None,
                ["gtk-disconnect", self.conf.name])
        self.queuing_iter = treestore.append(self.server_iter,
                ["gtk-media-play", _("Queuing")])
        self.completed_iter = treestore.append(self.server_iter,
                ["gtk-apply", _("Completed")])
        self.recycled_iter = treestore.append(self.server_iter,
                ["gtk-cancel", _("Recycled")])
        # Category Iters
        self.cate_iters = {}
        for cate_name in self.cates:
            cate_iter = treestore.append(self.completed_iter,
                    ["gtk-directory", cate_name[5:]])
            self.cate_iters[cate_name] = cate_iter
        self.treeview = treeview
        self.treestore = treestore

    def __get_conn_str(self):
        """
        Generate a connection string used by xmlrpc.
        """
        return 'http://%(user)s:%(passwd)s@%(host)s:%(port)s/rpc' % self.conf

class ServerView:
    """
    Aria2 server treeview in the left pane.
    """
    def __init__(self, main_window, treeview, treestore):
        # TreeSelection
        selection = treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect("changed", self.on_selection_changed)
        # TreeModel
        server_list = main_window.conf_file.main.servers.split(',')
        servers = {}
        server_conf_file = ConfigFile(U_SERVER_CONFIG_FILE)
        for server in server_list:
            server_conf = server_conf_file[server]
            server_cates = main_window.conf_file.cate[server].split(',')
            server_model = ServerModel(self, treestore, 
                    server_conf, server_cates)
            servers[server] = server_model

        self.main_win = main_window
        self.treeview = treeview
        self.treestore = treestore
        self.selection = selection
        self.server_list = server_list
        self.servers = servers

    def on_selection_changed(self, selection, data = None):
        """
        TreeView selection changed callback, changing the model of
        TaskView according to the selected row.
        """
        pass

