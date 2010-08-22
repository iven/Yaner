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
import glib
import gobject
from subprocess import Popen
from twisted.web import xmlrpc
from twisted.internet.error import ConnectionRefusedError, ConnectionLost

from Yaner.Category import Category
from Yaner.Constants import *
from Yaner.Constants import _
from Yaner.Configuration import ConfigFile

class Server:
    """
    Tree model for each aria2 server of the left pane in the main window.
    This contains queuing, completed, recycled tasks as its children.
    'group': the ServerGroup which the Server is in.
    'iters': iters list.
    'model': tasklist models of each iter.
    'proxy': xmlrpc server proxy.
    'connected: a boolean if the xmlrpc server is connected.
    """

    instances = {}

    def __init__(self, group, server_uuid):
        model = group.model
        # Preferences
        self.group = group
        self.uuid = server_uuid
        self.connected = False
        self.conf = ConfigFile.instances[self.uuid]
        self.proxy = xmlrpc.Proxy(self.__get_conn_str())
        # Iters
        server_iter = model.append(None,
                ["gtk-disconnect", self.get_name()])
        self.iters = [
                server_iter,
                model.append(server_iter, ["gtk-media-play", _("Queuing")]),
                model.append(server_iter, ["gtk-apply", _("Completed")]),
                model.append(server_iter, ["gtk-cancel", _("Recycled")]),
                ]
        for cate_uuid in self.get_cate_uuids():
            cate = Category(self, cate_uuid)
            cate_iter = model.append(self.iters[ITER_COMPLETED],
                    ["gtk-directory", cate.get_name()])
            cate.set_iter(cate_iter)
            self.iters.append(cate_iter)
        # Models
        self.models = []
        for i in xrange(len(self.iters)):
            model = gtk.TreeStore(
                    gobject.TYPE_STRING, # gid
                    gobject.TYPE_STRING, # status
                    gobject.TYPE_STRING, # name
                    gobject.TYPE_FLOAT,  # progress value
                    gobject.TYPE_STRING, # progress text
                    gobject.TYPE_STRING, # size
                    gobject.TYPE_STRING, # download speed
                    gobject.TYPE_STRING, # upload speed
                    gobject.TYPE_INT,    # connections
                    gobject.TYPE_STRING, # uuid
                    )
            self.models.append(model)

        # Add self to the global dict
        self.instances[self.uuid] = self

    def __get_conn_str(self):
        """
        Generate a connection string used by xmlrpc.
        """
        return 'http://%(user)s:%(passwd)s@%(host)s:%(port)s/rpc' \
                % self.conf.info

    def set_connected(self, connected):
        """
        Set if client is connected to the server.
        """
        self.connected = connected
        self.group.model.set(self.iters[ITER_SERVER], 0,
                'gtk-connect' if connected else 'gtk-disconnect')

    def get_name(self):
        """
        Get server name.
        """
        return self.conf.info.name

    def get_cate_uuids(self):
        """
        Get server category uuids.
        """
        cate_uuids = self.conf.info.cates.split(',')
        return cate_uuids if cate_uuids != [''] else []

    def get_cates(self):
        """
        Get server category instances.
        """
        return [Category.instances[cate_uuid]
                for cate_uuid in self.get_cate_uuids()]

    def get_session_info(self):
        """
        Call aria2 server for session info.
        """
        deferred = self.proxy.callRemote("aria2.getSessionInfo")
        deferred.addCallbacks(self.connect_ok, self.connect_error)
        deferred.addCallback(self.check_session)
        return False

    def get_session(self):
        """
        Get session id from config file.
        """
        return self.conf.info.session

    def set_session(self, session):
        """
        Set new session id in config file.
        """
        self.conf.info.session = session

    def check_session(self, session_info):
        """
        Check if aria2c is still last session.
        """
        is_new_session = (self.get_session() != session_info['sessionId'])
        self.set_session(session_info['sessionId'])
        for cate in self.get_cates():
            for task_uuid in cate.get_task_uuids():
                task_conf = ConfigFile.instances[task_uuid]
                if is_new_session:
                    # gid is useless, set it to '' to avoid updating iter.
                    task_conf.info['gid'] = ''
                cate.add_task(None, None, task_conf)

    def connect_ok(self, rtnval):
        """
        When connection succeeded, set "connected" to True.
        """
        self.set_connected(True)
        return rtnval

    def connect_error(self, failure):
        """
        When connection refused, set "connected" to False.
        """
        # XXX: Other errors?
        failure.check(ConnectionRefusedError, ConnectionLost)
        self.set_connected(False)

        return failure

class LocalServer(Server):
    """
    Server class for localhost.
    """

    def __init__(self, group, server_uuid):
        Server.__init__(self, group, server_uuid)
        # open aria2c server
        self.server_process = Popen([
            'aria2c', '--enable-xml-rpc', '--xml-rpc-listen-all',
            '--xml-rpc-listen-port=%s' % self.conf.info.port,
            '--xml-rpc-user=%s' % self.conf.info.user,
            '--xml-rpc-passwd=%s' % self.conf.info.passwd
            ])

class ServerGroup:
    """
    Aria2 server group in the treeview of the left pane.
    """
    def __init__(self, main_app, view):
        self.main_app = main_app
        self.model = view.get_model()
        # TreeSelection
        selection = view.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect("changed", self.on_selection_changed)
        self.selection = selection
        # TreeModel
        for server_uuid in self.get_server_uuids():
            if server_uuid == LOCAL_SERVER_UUID:
                server = LocalServer(self, server_uuid)
                view.expand_row('0', True)
                self.select_iter(server.iters[ITER_QUEUING])
            else:
                Server(self, server_uuid)
        for server in Server.instances.itervalues():
            glib.timeout_add_seconds(1, server.get_session_info)

    def get_server_uuids(self):
        """
        Get server uuids according to the order in the main config.
        """
        server_uuids = self.main_app.conf.info.servers.split(',')
        if server_uuids == ['']:
            server_uuids = []
        server_uuids.insert(0, LOCAL_SERVER_UUID)
        return server_uuids

    def get_servers(self):
        """
        Get server instances according to the order in the main config.
        """
        return [Server.instances[server_uuid]
                for server_uuid in self.get_server_uuids()]

    def select_iter(self, citer):
        """
        Set selected iter, and update task list view.
        """
        self.selection.select_iter(citer)

    def on_selection_changed(self, selection):
        """
        TreeView selection changed callback, changing the model of
        TaskView according to the selected row.
        """
        (model, selected_iter) = selection.get_selected()
        if isinstance(selected_iter, gtk.TreeIter):
            path = model.get_path(selected_iter)
            # if not the server iter
            if len(path) > 1:
                model_index = path[-1] + (1, ITER_COUNT)[len(path) - 2]
                server = self.get_servers()[path[0]]
                tasklist_model = server.models[model_index]
                self.main_app.tasklist_view.set_model(tasklist_model)

