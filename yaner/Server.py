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
from twisted.web import xmlrpc

from yaner.Constants import _

class Aria2Server:
    "Aria2 Server"

    def __init__(self, server_info, server_model):
        self.conn_str = 'http://%(user)s:%(passwd)s@%(host)s:%(port)s/rpc' \
                % server_info
        self.proxy = xmlrpc.Proxy(self.conn_str)
        self.info = server_info
        self.model = server_model

class Aria2ServerModel:
    """
    Aria2 server tree model of the left pane in the main window.
    This contains queuing, completed, recycled tasks as its children.
    """

    def __init__(self, model, server_info):
        self.server = Aria2Server(server_info, self)
        self.iter = model.append(None, ["gtk-add", server_name])
        self.queuing_iter = model.append(self.iter, ["gtk-add", _("Queuing")])
        self.completed_iter = model.append(self.iter, ["gtk-add", _("Completed")])
        self.recycled_iter = model.append(self.iter, ["gtk-add", _("Recycled")])
        self.model = model

