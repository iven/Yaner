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
    This file contains the main application class of Yaner, mostly
GUI related.
"""

import gtk
import os
import shutil
from twisted.internet import reactor

from yaner.Constants import *
from yaner.Server import ServerGroup
from yaner.Task import NormalTask, BTTask, MetalinkTask
from yaner.TaskNew import TaskNew
from yaner.Configuration import ConfigFile
from yaner.SingleInstance import SingleInstanceApp

class YanerApp(SingleInstanceApp):
    "Main Application"

    def __init__(self):
        SingleInstanceApp.__init__(self, "yaner")
        # Init paths
        self.init_paths()
        # Builder
        builder = gtk.Builder()
        builder.add_from_file(MAIN_UI_FILE)
        builder.connect_signals(self)
        self.builder = builder
        # Main Window
        self.main_window = builder.get_object("main_window")
        self.init_rgba(self.main_window)
        # Main Config
        self.conf = ConfigFile(U_MAIN_CONFIG_FILE)
        # Server View
        server_tv = builder.get_object("server_tv")
        self.server_group = ServerGroup(self, server_tv)
        # Task List View
        self.tasklist_view = builder.get_object('tasklist_tv')
        # Task New
        self.task_new = TaskNew(self)
        # Show the window
        self.main_window.show()

    @staticmethod
    def init_rgba(window):
        """
        Init rgba.
        """
        screen = window.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap:
            gtk.widget_set_default_colormap(colormap)

    @staticmethod
    def init_paths():
        """
        Init UConfigDir and config files.
        """
        if not os.path.exists(U_TASK_CONFIG_DIR):
            os.makedirs(U_TASK_CONFIG_DIR)
        if not os.path.exists(U_MAIN_CONFIG_FILE):
            shutil.copy(MAIN_CONFIG_FILE, U_CONFIG_DIR)
        if not os.path.exists(U_SERVER_CONFIG_FILE):
            shutil.copy(SERVER_CONFIG_FILE, U_CONFIG_DIR)

    def on_instance_exists(self):
        """
        Being called when another instance exists. Currently just quits.
        """
        SingleInstanceApp.on_instance_exists(self)


    def on_task_new_action_activate(self, action):
        """
        Being called when task_new_action activated.
        """
        self.task_new.run_dialog(action)

    def on_task_remove_action_activate(self, action):
        """
        Being called when task_remove_action activated.
        """
        pass

    def on_task_start_action_activate(self, action):
        """
        Being called when task_start_action activated.
        """
        pass

    def on_task_pause_action_activate(self, action):
        """
        Being called when task_pause_action activated.
        """
        pass

    @staticmethod
    def on_about_action_activate(about_dialog):
        """
        Show about dialog.
        """
        about_dialog.set_version(VERSION)
        about_dialog.run()
        about_dialog.hide()
        
    @staticmethod
    def on_quit_action_activate(action):
        """
        Main window quit callback.
        """
        gtk.widget_pop_colormap()
        reactor.stop()

if __name__ == '__main__':
    YanerApp()
    gtk.main()
