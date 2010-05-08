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

from yaner.Constants import *
from yaner.Server import ServerView
from yaner.Configuration import ConfigFile
from yaner.SingleInstance import SingleInstanceApp

class YanerApp(SingleInstanceApp):
    "Main Application"

    def __init__(self):
        SingleInstanceApp.__init__(self, "yaner")
        # Builder
        self.builder = gtk.Builder()
        self.builder.add_from_file(GLADE_FILE)
        self.builder.connect_signals(self)
        #
        self.main_window = self.builder.get_object("main_window")
        #
        self.init_rgba()
        self.init_paths()
        self.init_filefilters()
        # Main Config
        self.conf_file = ConfigFile(U_MAIN_CONFIG_FILE)
        # Server View
        server_tv = self.builder.get_object("server_tv")
        server_ts = self.builder.get_object("server_ts")
        self.server_view = ServerView(self, server_tv, server_ts)
        # Task New Dialog
        self.task_new_dialog = self.builder.get_object("task_new_dialog")
        self.task_new_nb = self.builder.get_object("task_new_nb")
        self.task_new_server_cb = self.builder.get_object("task_new_server_cb")
        self.task_new_server_ls = self.builder.get_object("task_new_server_ls")
        self.task_new_cate_cb = self.builder.get_object("task_new_cate_cb")
        self.task_new_cate_ls = self.builder.get_object("task_new_cate_ls")
        self.task_new_dir_entry = self.builder.get_object("task_new_dir_entry")
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

    @staticmethod
    def init_paths():
        """
        Init UConfigDir and config files.
        """
        if not os.path.exists(U_CONFIG_DIR):
            os.makedirs(U_CONFIG_DIR)
        if not os.path.exists(U_MAIN_CONFIG_FILE):
            shutil.copy(MAIN_CONFIG_FILE, U_CONFIG_DIR)
        if not os.path.exists(U_SERVER_CONFIG_FILE):
            shutil.copy(SERVER_CONFIG_FILE, U_CONFIG_DIR)

    def init_filefilters(self):
        """
        Init Filefilters.
        """
        torrent_filefilter = self.builder.get_object("torrent_filefilter")
        torrent_filefilter.add_mime_type("application/x-bittorrent")
        metalink_filefilter = self.builder.get_object("metalink_filefilter")
        metalink_filefilter.add_mime_type("application/xml")

    def on_instance_exists(self):
        """
        Being called when another instance exists. Currently just quits.
        """
        SingleInstanceApp.on_instance_exists(self)

    def on_task_new_dir_chooser_changed(self, widget):
        """
        When directory chooser selection changed, update the directory entry.
        """
        directory = widget.get_filename()
        self.task_new_dir_entry.set_text(directory)

    def on_task_new_cate_cb_changed(self, widget):
        """
        When category combobox selection changed, update the directory entry.
        """
        model = widget.get_model()
        aiter = widget.get_active_iter()
        if aiter != None:
            directory = model.get(aiter, 1)[0]
            self.task_new_dir_entry.set_text(directory)

    def on_task_new_server_cb_changed(self, widget):
        """
        When server combobox selection changed, update the category combobox.
        """
        model = widget.get_model()
        aiter = widget.get_active_iter()
        if aiter != None:
            server = model.get(aiter, 1)[0]
            server_model = self.server_view.servers[server]
            self.task_new_cate_ls.clear()
            for cate_name in server_model.cates:
                directory = server_model.conf[cate_name]
                self.task_new_cate_ls.append([cate_name[5:], directory])
            self.task_new_cate_cb.set_active(0)

    def on_task_new_action_activate(self, action):
        """
        Popup new task dialog and process.
        """
        # set current page of the notebook
        action_dict = {
                "task_new_normal_action": TASK_NORMAL,
                "task_new_bt_action": TASK_BT,
                "task_new_metalink_action": TASK_METALINK,
                }
        page = action_dict[action.get_property('name')]
        self.task_new_nb.set_current_page(page)
        # init the server cb
        self.task_new_server_ls.clear()
        for server in self.server_view.server_list:
            model = self.server_view.servers[server]
            self.task_new_server_ls.append([model.conf.name, server])
        self.task_new_server_cb.set_active(0)
        # run the dialog
        response = self.task_new_dialog.run()
        self.task_new_dialog.hide()
        if response == gtk.RESPONSE_OK:
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
    def on_quit_action_activate(widget):
        """
        Main window quit callback.
        """
        gtk.widget_pop_colormap()
        gtk.main_quit()

if __name__ == '__main__':
    YanerApp()
    gtk.main()
