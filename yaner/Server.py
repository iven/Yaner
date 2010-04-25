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

class Server:
    "Aria2 Server"

    def __init__(self, server_model, server_conf):
        self.info = server_conf.information
        self.cate = server_conf.category
        self.conn_str = 'http://%(user)s:%(passwd)s@%(host)s:%(port)s/rpc' \
                % self.info
        self.proxy = xmlrpc.Proxy(self.conn_str)
        self.model = server_model

class ServerModel:
    """
    Aria2 server tree model of the left pane in the main window.
    This contains queuing, completed, recycled tasks as its children.
    """

    def __init__(self, treeview, treestore, server_conf):
        self.server = Server(self, server_conf)
        self.iter = treestore.append(None, ["gtk-disconnect", self.server.info.name])
        self.queuing_iter = treestore.append(self.iter, ["gtk-media-forward", _("Queuing")])
        self.completed_iter = treestore.append(self.iter, ["gtk-media-stop", _("Completed")])
        self.recycled_iter = treestore.append(self.iter, ["gtk-media-rewind", _("Recycled")])
        for (name, path) in self.server.cate.items():
            iter = treestore.append(self.completed_iter, ["gtk-add", name])
        self.treeview = treeview
        self.treestore = treestore

class ServerView:
    """
    Aria2 server treeview in the left pane.
    """
    def __init__(self, main_window, treeview, treestore):
        selection = treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)

        for f in os.listdir(UServerConfigDir):
            if f.endswith('.conf'):
                server_conf = ConfigFile(os.path.join(UServerConfigDir, f))
                ServerModel(self, treestore, server_conf)

        self.main_win = main_window
        self.treeview = treeview
        self.treestore = treestore
