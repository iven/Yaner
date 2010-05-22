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

from yaner.Constants import U_SERVER_CONFIG_FILE, ITER_COMPLETED
from yaner.Constants import _
from yaner.Configuration import ConfigFile
from yaner.ODict import ODict

class Server:
    """
    Tree model for each aria2 server of the left pane in the main window.
    This contains queuing, completed, recycled tasks as its children.
    'group': the ServerGroup which the Server is in.
    'conf': the server ConfigFile.
    'iter': iter of the server itself.
    'cates': the categories list of the server.
    'iters': iters list other than server iter.
    'model': tasklist models of each iter.
    'proxy': xmlrpc server proxy.
    'connected: a boolean if the xmlrpc server is connected.
    """

    def __init__(self, group, conf):
        store = group.store
        # Preferences
        self.group = group
        self.conf = conf
        self.connected = False
        self.proxy = xmlrpc.Proxy(self.__get_conn_str())
        # Categories
        self.cates = conf.cates.split(',')
        # Iters
        self.iter = store.append(None, ["gtk-disconnect", conf.name])
        self.iters = [
                store.append(self.iter, ["gtk-media-play", _("Queuing")]),
                store.append(self.iter, ["gtk-apply", _("Completed")]),
                store.append(self.iter, ["gtk-cancel", _("Recycled")]),
                ]
        for cate_name in self.cates:
            cate_iter = store.append(self.iters[ITER_COMPLETED],
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
        self.group.store.set(self.iter, 0,
                'gtk-connect' if connected else 'gtk-disconnect')

class ServerGroup:
    """
    Aria2 server group in the treeview of the left pane.
    """
    def __init__(self, main_app, view, store):
        self.main_app = main_app
        self.view = view
        self.store = store
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
        #(model, selected_iter) = selection.get_selected()
        pass

