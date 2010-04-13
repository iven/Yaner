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

from yaner.Constants import *
from yaner.SingleInstance import SingleInstanceApp

class YanerApp(SingleInstanceApp):
    "Main Application"

    def __init__(self):
        SingleInstanceApp.__init__(self, "yaner")
        builder = gtk.Builder()
        builder.add_from_file(GladeFile)
        self.main_window = builder.get_object("main_window")
        self.about_dialog = builder.get_object("about_dialog")
        builder.connect_signals(self)

        self.main_window.show()

    def on_instance_exists(self):
        SingleInstanceApp.on_instance_exists(self)

    def on_new_action_activate(self, widget, data = None):
        pass

    def on_about_action_activate(self, widget, data = None):
        self.about_dialog.show()
        
    def on_quit_action_activate(self, widget, data = None):
        self.on_quit()

    def on_main_window_destroy(self, widget, data = None):
        self.on_quit()

    def on_quit(self):
        gtk.main_quit()

if __name__ == '__main__':
    YanerApp()
    gtk.main()
