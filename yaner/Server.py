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

class ServerView:
    """
    Aria2 server treeview in the left pane.
    """
    def __init__(self, main_app, view, store):
        self.main_app = main_app
        self.view = view
        self.store = store
        self.servers = ODict()
        # TreeModel
        self.conf = ConfigFile(U_SERVER_CONFIG_FILE)
        for server in main_app.conf.main.servers.split(','):
            self.servers[server] = self.__init_server(server)
        # TreeSelection
        selection = view.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect("changed", self.on_selection_changed)

    def __init_server(self, server):
        """
        Generate the server dict by server name.
        'conf': the server ConfigFile.
        'cates': the categories list of the server.
        'iter': iter of the server itself.
        'iters': a dict with iters as keys and tasklist models as values.
        'proxy': xmlrpc server proxy.
        'connected: a boolean if the xmlrpc server is connected.
        TODO: Add 'models'
        """
        s_dict = ODict()
        s_dict['conf'] = self.conf[server]
        s_dict['cates'] = self.main_app.conf.cate[server].split(',')
        s_dict['iters'] = ODict()
        # Generate iters list
        store = self.store
        s_dict['iter'] = store.append(None,
                ["gtk-disconnect", s_dict['conf'].name])
        iters_list = [
                store.append(s_dict['iter'], ["gtk-media-play", _("Queuing")]),
                store.append(s_dict['iter'], ["gtk-apply", _("Completed")]),
                store.append(s_dict['iter'], ["gtk-cancel", _("Recycled")]),
                ]
        for cate_name in s_dict['cates']:
            cate_iter = store.append(iters_list[ITER_COMPLETED],
                    ["gtk-directory", cate_name[5:]])
            iters_list.append(cate_iter)
        # Create a model for each iter for tasklist treeview
        for key in iters_list:
            s_dict['iters'][key] = gtk.TreeStore(
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
        s_dict['proxy'] = xmlrpc.Proxy(self.__get_conn_str(s_dict['conf']))
        s_dict['connected'] = False

        return s_dict

    @staticmethod
    def __get_conn_str(attr_dict):
        """
        Generate a connection string used by xmlrpc.
        """
        return 'http://%(user)s:%(passwd)s@%(host)s:%(port)s/rpc' % attr_dict

    def server_set_connected(self, server, connected):
        """
        Set if client is connected to the server.
        """
        s_dict = self.servers[server]
        s_dict['connected'] = connected
        self.store.set(s_dict['iter'], 0,
                'gtk-connect' if connected else 'gtk-disconnect')

    def on_selection_changed(self, selection):
        """
        TreeView selection changed callback, changing the model of
        TaskView according to the selected row.
        """
        #(model, selected_iter) = selection.get_selected()
        pass

