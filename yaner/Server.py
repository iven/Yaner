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

import pygtk
import gtk
import os
from twisted.web import xmlrpc

from yaner.Constants import *
from yaner.Constants import _
from yaner.Configuration import *

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
        self.conn_str = 'http://%(user)s:%(passwd)s@%(host)s:%(port)s/rpc' \
                % self.conf
        self.proxy = xmlrpc.Proxy(self.conn_str)
        # Iters
        self.iter = treestore.append(None, ["gtk-disconnect", self.conf.name])
        self.queuing_iter = treestore.append(self.iter, ["gtk-media-play", _("Queuing")])
        self.completed_iter = treestore.append(self.iter, ["gtk-apply", _("Completed")])
        self.recycled_iter = treestore.append(self.iter, ["gtk-cancel", _("Recycled")])
        # Category Iters
        self.cate_iters = {}
        for cate_name in self.cates:
            key_name = 'cate_' + cate_name
            iter = treestore.append(self.completed_iter, ["gtk-directory", cate_name])
            self.cate_iters[cate_name] = iter
        self.treeview = treeview
        self.treestore = treestore

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
        servers = {}
        server_conf_file = ConfigFile(UServerConfigFile)
        for server in main_window.conf_file.main.servers.split(','):
            server_conf = getattr(server_conf_file, server)
            server_cates = getattr(main_window.conf_file.cate, server).split(',')
            server_model = ServerModel(self, treestore, server_conf, server_cates)
            servers[server] = server_model

        self.main_win = main_window
        self.treeview = treeview
        self.treestore = treestore
        self.selection = selection
        self.servers = servers

    def on_selection_changed(self, selection, data = None):
        pass

