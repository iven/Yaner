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
from yaner.Server import *
from yaner.SingleInstance import *

class YanerApp(SingleInstanceApp):
    "Main Application"

    def __init__(self):
        SingleInstanceApp.__init__(self, "yaner")
        # Builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(GladeFile)
        self.builder.connect_signals(self)
        # Windows
        self.main_window = self.builder.get_object("main_window")
        self.about_dialog = self.builder.get_object("about_dialog")
        self.about_dialog.set_version(Version)
        self.task_new_dialog = self.builder.get_object("task_new_dialog")
        # Server View
        server_tv = self.builder.get_object("server_tv")
        server_ts = self.builder.get_object("server_ts")
        self.server_view = ServerView(self, server_tv, server_ts);
        #
        self.init_rgba()
        self.init_paths()
        self.init_filefilters()
        # Show the window
        self.main_window.show()

    def init_rgba(self):
        """
        Init rgba.
        """
        screen = self.main_window.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap:
            gtk.widget_set_default_colormap(colormap)

    def init_paths(self):
        """
        Init UConfigDir and config files.
        """
        if not os.path.exists(UServerConfigDir):
            os.makedirs(UServerConfigDir)
            shutil.copy(ServerConfigFile, UServerConfigDir)

    def init_filefilters(self):
        """
        Init Filefilters.
        """
        torrent_filefilter = self.builder.get_object("torrent_filefilter")
        torrent_filefilter.add_mime_type("application/x-bittorrent")
        metalink_filefilter = self.builder.get_object("metalink_filefilter")
        metalink_filefilter.add_mime_type("application/xml")

    def on_instance_exists(self):
        SingleInstanceApp.on_instance_exists(self)

    def on_task_new_action_activate(self, widget, data = None):
        self.task_new_dialog.run()
        self.task_new_dialog.hide()

    def on_about_action_activate(self, widget, data = None):
        self.about_dialog.run()
        self.about_dialog.hide()
        
    def on_quit_action_activate(self, widget, data = None):
        self.on_quit()

    def on_main_window_destroy(self, widget, data = None):
        self.on_quit()

    def on_quit(self):
        gtk.widget_pop_colormap()
        gtk.main_quit()

if __name__ == '__main__':
    YanerApp()
    gtk.main()
