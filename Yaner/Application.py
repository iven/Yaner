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
import glob
import shutil
from twisted.internet import reactor

from Yaner.Constants import *
from Yaner.Server import ServerGroup, Server
from Yaner.TaskNew import TaskNew
from Yaner.Configuration import ConfigFile
from Yaner.SingleInstance import SingleInstanceApp

class YanerApp(SingleInstanceApp):
    "Main Application"

    def __init__(self):
        SingleInstanceApp.__init__(self, "yaner")
        # Init paths
        self.__init_paths()
        # Init Config
        self.__init_confs()
        self.conf = ConfigFile.instances[U_MAIN_CONFIG_UUID]
        # Builder
        builder = gtk.Builder()
        builder.set_translation_domain('yaner')
        builder.add_from_file(MAIN_UI_FILE)
        builder.connect_signals(self)
        self.builder = builder
        # Main Window
        self.main_window = builder.get_object("main_window")
        self.__init_rgba(self.main_window)
        # Server View
        server_tv = builder.get_object("server_tv")
        self.server_group = ServerGroup(self, server_tv)
        # Task List View
        self.tasklist_view = builder.get_object('tasklist_tv')
        selection = self.tasklist_view.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        # Task New
        self.task_new = TaskNew(self)
        # Show the window
        self.main_window.show()

    @staticmethod
    def __init_rgba(window):
        """
        Init rgba.
        """
        screen = window.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap:
            gtk.widget_set_default_colormap(colormap)

    @staticmethod
    def __init_paths():
        """
        Create UConfigDir and config files during first start.
        """
        if not os.path.exists(U_CONFIG_DIR):
            os.makedirs(U_TASK_CONFIG_DIR)
            os.makedirs(U_CATE_CONFIG_DIR)
            os.makedirs(U_SERVER_CONFIG_DIR)
            shutil.copy(MAIN_CONFIG_FILE, U_CONFIG_DIR)
            shutil.copy(LOCAL_CATE_CONFIG_FILE, U_CATE_CONFIG_DIR)
            shutil.copy(LOCAL_SERVER_CONFIG_FILE, U_SERVER_CONFIG_DIR)

    @staticmethod
    def __init_confs():
        """
        Read config files during start.
        """
        conf_dirs = {
                U_CONFIG_DIR: '*.conf',
                U_TASK_CONFIG_DIR: '*',
                U_CATE_CONFIG_DIR: '*',
                U_SERVER_CONFIG_DIR: '*',
                }
        for (conf_dir, wildcard) in conf_dirs.iteritems():
            for conf_file in glob.glob(os.path.join(conf_dir, wildcard)):
                ConfigFile(conf_file)

    def get_default_options(self):
        """
        Get task default options.
        """
        return dict(self.conf.default)

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
        # Kill local aria2c process
        Server.instances[LOCAL_SERVER_UUID].server_process.terminate()
        gtk.widget_pop_colormap()
        reactor.stop()

if __name__ == '__main__':
    YanerApp()
    gtk.main()
