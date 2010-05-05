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
        #
        self.main_window = self.builder.get_object("main_window")
        #
        self.init_rgba()
        self.init_paths()
        self.init_filefilters()
        # Main Config
        self.conf_file = ConfigFile(UMainConfigFile)
        # Server View
        server_tv = self.builder.get_object("server_tv")
        server_ts = self.builder.get_object("server_ts")
        self.server_view = ServerView(self, server_tv, server_ts);
        # About Dialog
        self.about_dialog = self.builder.get_object("about_dialog")
        self.about_dialog.set_version(Version)
        # Task New Dialog
        self.task_new_dialog = self.builder.get_object("task_new_dialog")
        self.task_new_nb = self.builder.get_object("task_new_nb")
        self.task_new_server_combobox = self.builder.get_object("task_new_server_combobox")
        self.task_new_server_ls = self.builder.get_object("task_new_server_ls")
        self.task_new_cate_combobox = self.builder.get_object("task_new_cate_combobox")
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

    def init_paths(self):
        """
        Init UConfigDir and config files.
        """
        if not os.path.exists(UConfigDir):
            os.makedirs(UConfigDir)
        if not os.path.exists(UMainConfigFile):
            shutil.copy(MainConfigFile, UConfigDir)
        if not os.path.exists(UServerConfigFile):
            shutil.copy(ServerConfigFile, UConfigDir)

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

    def on_task_new_dir_chooser_selection_changed(self, widget, data = None):
        dir = widget.get_filename()
        self.task_new_dir_entry.set_text(dir)

    def on_task_new_cate_combobox_changed(self, widget, data = None):
        model = widget.get_model()
        iter = widget.get_active_iter()
        if iter != None:
            dir = model.get(iter, 1)[0]
            self.task_new_dir_entry.set_text(dir)

    def on_task_new_server_combobox_changed(self, widget, data = None):
        model = widget.get_model()
        iter = widget.get_active_iter()
        if iter != None:
            server = model.get(iter, 1)[0]
            server_model = self.server_view.servers[server]
            self.task_new_cate_ls.clear()
            for cate_name in server_model.cates:
                dir = server_model.conf[cate_name]
                self.task_new_cate_ls.append([cate_name[5:], dir])
            self.task_new_cate_combobox.set_active(0)

    def on_task_new_action_activate(self, action, data = None):
        # set current page of the notebook
        action_dict = {
                "task_new_normal_action": TASK_NORMAL,
                "task_new_bt_action": TASK_BT,
                "task_new_metalink_action": TASK_METALINK,
                }
        page = action_dict[action.get_property('name')]
        self.task_new_nb.set_current_page(page)
        # init the server combobox
        self.task_new_server_ls.clear()
        for server in self.server_view.server_list:
            model = self.server_view.servers[server]
            iter = self.task_new_server_ls.append([model.conf.name, server])
        self.task_new_server_combobox.set_active(0)
        # run the dialog
        response = self.task_new_dialog.run()
        self.task_new_dialog.hide()
        if response == gtk.RESPONSE_OK:
            pass

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
