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
        builder = gtk.Builder()
        builder.add_from_file(GLADE_FILE)
        builder.connect_signals(self)
        # Main Window
        self.main_window = builder.get_object("main_window")
        # File Filters
        filefilters = {}
        filefilters['torrent'] = builder.get_object("torrent_filefilter")
        filefilters['metalink'] = builder.get_object("metalink_filefilter")
        #
        self.init_rgba(self.main_window)
        self.init_paths()
        self.init_filefilters(filefilters)
        # Main Config
        self.conf_file = ConfigFile(U_MAIN_CONFIG_FILE)
        # Server View
        server_tv = builder.get_object("server_tv")
        server_ts = builder.get_object("server_ts")
        self.server_view = ServerView(self, server_tv, server_ts)
        # Task New Dialog
        self.task_new_dialog = builder.get_object("task_new_dialog")
        self.task_new_widgets = self.task_new_get_widgets(builder)
        self.task_new_prefs = self.task_new_get_prefs(builder)
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
        if not os.path.exists(U_CONFIG_DIR):
            os.makedirs(U_CONFIG_DIR)
        if not os.path.exists(U_MAIN_CONFIG_FILE):
            shutil.copy(MAIN_CONFIG_FILE, U_CONFIG_DIR)
        if not os.path.exists(U_SERVER_CONFIG_FILE):
            shutil.copy(SERVER_CONFIG_FILE, U_CONFIG_DIR)

    @staticmethod
    def init_filefilters(filefilters):
        """
        Init Filefilters.
        """
        filefilters['torrent'].add_mime_type("application/x-bittorrent")
        filefilters['metalink'].add_mime_type("application/xml")

    @staticmethod
    def task_new_get_widgets(builder):
        """
        Get a dict of widget of new task dialog for future use.
        """
        widgets = {}
        widgets['nb'] = builder.get_object("task_new_nb")

        widgets['server_cb'] = builder.get_object("task_new_server_cb")
        widgets['server_ls'] = builder.get_object("task_new_server_ls")
        widgets['cate_cb'] = builder.get_object("task_new_cate_cb")
        widgets['cate_ls'] = builder.get_object("task_new_cate_ls")

        widgets['normal_uri_textview'] = builder.get_object(
                "task_new_normal_uri_textview")
        widgets['bt_uri_textview'] = builder.get_object(
                "task_new_bt_uri_textview")
        widgets['bt_file_chooser'] = builder.get_object(
                "task_new_bt_file_chooser")
        widgets['metalink_file_chooser'] = builder.get_object(
                "task_new_metalink_file_chooser")
        return widgets

    @staticmethod
    def task_new_get_prefs(builder):
        """
        Get a dict of widget corresponding to a preference in the
        configuration file of new task dialog for future use.
        """
        prefs = {}
        prefs['split'] = builder.get_object('split_adjustment')
        prefs['bt-max-open-files'] = builder.get_object('max_files_adjustment')
        prefs['bt-max-peers'] = builder.get_object('max_peers_adjustment')
        prefs['seed-time'] = builder.get_object('seed_time_adjustment')
        prefs['seed-ratio'] = builder.get_object('seed_ratio_adjustment')
        prefs['metalink-servers'] = builder.get_object('servers_adjustment')
        prefs['dir'] = builder.get_object("task_new_dir_entry")
        prefs['metalink-location'] = builder.get_object(
                'task_new_location_entry')
        prefs['metalink-language'] = builder.get_object(
                'task_new_language_entry')
        return prefs

    def on_instance_exists(self):
        """
        Being called when another instance exists. Currently just quits.
        """
        SingleInstanceApp.on_instance_exists(self)

    def on_task_new_dir_chooser_changed(self, dir_chooser):
        """
        When directory chooser selection changed, update the directory entry.
        """
        directory = dir_chooser.get_filename()
        self.task_new_prefs['dir'].set_text(directory)

    def on_task_new_cate_cb_changed(self, cate_cb):
        """
        When category combobox selection changed, update the directory entry.
        """
        model = cate_cb.get_model()
        aiter = cate_cb.get_active_iter()
        if aiter != None:
            directory = model.get(aiter, 1)[0]
            self.task_new_prefs['dir'].set_text(directory)

    def on_task_new_server_cb_changed(self, server_cb):
        """
        When server combobox selection changed, update the category combobox.
        """
        model = server_cb.get_model()
        aiter = server_cb.get_active_iter()
        if aiter != None:
            server = model.get(aiter, 1)[0]
            server_model = self.server_view.servers[server]
            self.task_new_widgets['cate_ls'].clear()
            for cate_name in server_model.cates:
                directory = server_model.conf[cate_name]
                self.task_new_widgets['cate_ls'].append(
                        [cate_name[5:], directory])
            self.task_new_widgets['cate_cb'].set_active(0)

    def on_task_new_action_activate(self, action):
        """
        Popup new task dialog and process.
        """
        widgets = self.task_new_widgets
        default_conf = self.conf_file.default
        # set current page of the notebook
        action_dict = {
                "task_new_normal_action": TASK_NORMAL,
                "task_new_bt_action": TASK_BT,
                "task_new_metalink_action": TASK_METALINK,
                }
        page = action_dict[action.get_property('name')]
        widgets['nb'].set_current_page(page)
        # init default configuration
        for (pref, widget) in self.task_new_prefs.iteritems():
            if hasattr(widget, 'set_value'):
                widget.set_value(float(default_conf[pref]))
            elif hasattr(widget, 'set_text'):
                widget.set_text(default_conf[pref])
        # init the server cb
        widgets['server_ls'].clear()
        for (server, model) in self.server_view.servers.iteritems():
            widgets['server_ls'].append([model.conf.name, server])
        widgets['server_cb'].set_active(0)
        # run the dialog
        response = self.task_new_dialog.run()
        while response == gtk.RESPONSE_OK:
            if self.create_new_task():
                self.task_new_dialog.hide()
                break
            else:
                response = self.task_new_dialog.run()

    def create_new_task(self):
        """
        Create a new download task from default configuration
        and new task dialog.
        Returns True for success, False for failure.
        """
        widgets = self.task_new_widgets
        task_type = widgets['nb'].get_current_page()
        (uris, torrent, metalink) = (None,) * 3
        if task_type == TASK_METALINK:
            metalink = widgets['metalink_file_chooser'].get_filename()
            if not metalink:
                return False
        elif task_type == TASK_NORMAL:
            tbuffer = widgets['normal_uri_textview'].get_buffer()
        elif task_type == TASK_BT:
            tbuffer = widgets['bt_uri_textview'].get_buffer()
            torrent = widgets['bt_file_chooser'].get_filename()
            if not torrent:
                return False
        return True

#        if task_type in (TASK_NORMAL, TASK_BT):
#            start_iter = buff
#            uris = ""
#        # get server
#        model = widgets['server_cb'].get_model()
#        aiter = widgets['server_cb'].get_active_iter()
#        server = model.get(aiter, 1)[0]
#        # get category
#        model = widgets['cate_cb'].get_model()
#        aiter = widgets['cate_cb'].get_active_iter()
#        cate = 'cate_' + model.get(aiter, 0)[0]
#        # task options
#        task_options = default_conf.copy()
#        for (pref, widget) in self.task_new_prefs.iteritems():
#            if hasattr(widget, 'get_value'):
#                task_options[pref] = widget.get_value()
#            elif hasattr(widget, 'set_text'):
#                task_options[pref] = widget.get_text()
#
#        print server, cate, task_options

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
