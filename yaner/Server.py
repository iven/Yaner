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

class Aria2Server:
    "Aria2 Server"

    def __init__(self, host, port = 6800, user = '', passwd = ''):
        self.server_info = {
                'host': host,
                'port': port,
                'user': user,
                'passwd': passwd,
                }
        self.conn_str = 'http://%(user):%(passwd)@%(host):%(port)/rpc' \
                % self.server_info
        self.proxy = xmlrpc.Proxy(self.conn_str)


