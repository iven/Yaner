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
import shutil

from yaner.Constants import *
from yaner.Configuration import *
from yaner.Server import *
from yaner.SingleInstance import *

class YanerApp(SingleInstanceApp):
    "Main Application"

    def __init__(self):
        SingleInstanceApp.__init__(self, "yaner")
        builder = gtk.Builder()
        builder.add_from_file(GladeFile)
        self.main_window = builder.get_object("main_window")
        self.about_dialog = builder.get_object("about_dialog")
        self.server_ts = builder.get_object("server_ts")
        tmp_iter = Aria2ServerView(self.server_ts, "localhost")
        builder.connect_signals(self)

        self.init_paths()
        self.init_servers()

        self.main_window.show()

    def init_paths(self):
        """
        Init UConfigDir and config files.
        """
        if not os.path.exists(UConfigDir):
            os.makedirs(UConfigDir)
            shutil.copyfile(ServerConfigFile, UServerConfigFile)

    def init_servers(self):
        """
        Init servers, include GUI TreeView building.
        """
        server_conf = ConfigFile(UServerConfigFile)
        server_models = []
        for (server_name, server_info) in server_conf.items():
            server_models.append(Aria2ServerModel(self.server_ts, server_info))

    def on_instance_exists(self):
        SingleInstanceApp.on_instance_exists(self)

    def on_new_action_activate(self, widget, data = None):
        pass

    def on_about_action_activate(self, widget, data = None):
        self.about_dialog.run()
        self.about_dialog.hide()
        
    def on_quit_action_activate(self, widget, data = None):
        self.on_quit()

    def on_main_window_destroy(self, widget, data = None):
        self.on_quit()

    def on_quit(self):
        gtk.main_quit()

if __name__ == '__main__':
    YanerApp()
    gtk.main()
