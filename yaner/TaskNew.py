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
    This file contains the new task dialog of Yaner.
"""

import os
import gtk

from yaner.Constants import *
from yaner.Task import NormalTask, BTTask, MetalinkTask

class TaskNew:
    """
    This class contains widgets and methods related to new task dialog.
    """
    def __init__(self, main_app):
        # GTK+ Builder
        builder = gtk.Builder()
        builder.add_from_file(TASK_NEW_UI_FILE)
        builder.connect_signals(self)

        self.widgets = self.__get_widgets(builder)
        self.prefs = self.__get_prefs(builder)
        filefilters = self.__get_filefilters(builder)
        self.__init_filefilters(filefilters)

        self.main_app = main_app
    
    @staticmethod
    def __init_filefilters(filefilters):
        """
        Init Filefilters.
        """
        filefilters['torrent'].add_mime_type("application/x-bittorrent")
        filefilters['metalink'].add_mime_type("application/xml")

    @staticmethod
    def __get_filefilters(builder):
        """
        Get a dict of filefilters of new task dialog for future use.
        """
        filefilters = {}
        filefilters['torrent'] = builder.get_object("torrent_filefilter")
        filefilters['metalink'] = builder.get_object("metalink_filefilter")
        return filefilters

    @staticmethod
    def __get_widgets(builder):
        """
        Get a dict of widget of new task dialog for future use.
        """
        widgets = {}
        widgets['dialog'] = builder.get_object("dialog")
        widgets['nb'] = builder.get_object("nb")

        widgets['server_cb'] = builder.get_object("server_cb")
        widgets['server_ls'] = builder.get_object("server_ls")
        widgets['cate_cb'] = builder.get_object("cate_cb")
        widgets['cate_ls'] = builder.get_object("cate_ls")

        widgets['normal_uri_textview'] = builder.get_object(
                "normal_uri_textview")
        widgets['bt_uri_textview'] = builder.get_object(
                "bt_uri_textview")
        widgets['bt_file_chooser'] = builder.get_object(
                "bt_file_chooser")
        widgets['metalink_file_chooser'] = builder.get_object(
                "metalink_file_chooser")
        return widgets

    @staticmethod
    def __get_prefs(builder):
        """
        Get a dict of widget corresponding to a preference in the
        configuration file of new task dialog for future use.
        """
        prefs = {}
        prefs['dir'] = builder.get_object("dir_entry")
        prefs['out'] = builder.get_object("rename_entry")
        prefs['referer'] = builder.get_object("referer_entry")
        prefs['http-user'] = builder.get_object("http_user_entry")
        prefs['http-passwd'] = builder.get_object("http_pass_entry")
        prefs['ftp-user'] = builder.get_object("ftp_user_entry")
        prefs['ftp-passwd'] = builder.get_object("ftp_pass_entry")
        prefs['split'] = builder.get_object('split_adjustment')
        prefs['bt-max-open-files'] = builder.get_object('max_files_adjustment')
        prefs['bt-max-peers'] = builder.get_object('max_peers_adjustment')
        prefs['seed-time'] = builder.get_object('seed_time_adjustment')
        prefs['seed-ratio'] = builder.get_object('seed_ratio_adjustment')
        prefs['bt-prioritize-piece'] = builder.get_object(
                "prioritize_checkbutton")
        prefs['metalink-servers'] = builder.get_object(
                'servers_adjustment')
        prefs['metalink-location'] = builder.get_object(
                'location_entry')
        prefs['metalink-language'] = builder.get_object(
                'language_entry')
        prefs['metalink-os'] = builder.get_object(
                'os_adjustment')
        prefs['metalink-version'] = builder.get_object(
                'version_adjustment')
        return prefs

    @staticmethod
    def __get_uris(textview):
        """
        Get URIs from textviews, returning a tuple of URIs.
        """
        tbuffer = textview.get_buffer()
        uris = tbuffer.get_text(
                tbuffer.get_start_iter(),
                tbuffer.get_end_iter()
                )
        return [uri.strip() for uri in uris.split("\n") if uri.strip()]

    def run_dialog(self, action):
        """
        Popup new task dialog.
        """
        widgets = self.widgets
        default_conf = self.main_app.conf.default
        # set current page of the notebook
        actions = (
                "task_new_normal_action",
                "task_new_bt_action",
                "task_new_metalink_action",
                )
        page = actions.index(action.get_property('name'))
        widgets['nb'].set_current_page(page)
        # init default configuration
        for (pref, widget) in self.prefs.iteritems():
            if hasattr(widget, 'set_value'):
                widget.set_value(float(default_conf[pref]))
            elif hasattr(widget, 'set_text'):
                widget.set_text(default_conf[pref])
        # init the server cb
        widgets['server_ls'].clear()
        for server in self.main_app.server_group.servers.itervalues():
            widgets['server_ls'].append([server.conf.name, ])
        widgets['server_cb'].set_active(0)
        # run the dialog
        widgets['dialog'].run()
        
    def on_dir_chooser_changed(self, dir_chooser):
        """
        When directory chooser selection changed, update the directory entry.
        """
        directory = dir_chooser.get_filename()
        self.prefs['dir'].set_text(directory)

    def on_cate_cb_changed(self, cate_cb):
        """
        When category combobox selection changed, update the directory entry.
        """
        active_iter = cate_cb.get_active_iter()
        if active_iter != None:
            model = self.widgets['cate_ls']
            directory = model.get(active_iter, 1)[0]
            self.prefs['dir'].set_text(directory)

    def on_server_cb_changed(self, server_cb):
        """
        When server combobox selection changed, update the category combobox.
        """
        index = server_cb.get_active()
        if index != -1:
            server = self.main_app.server_group.servers.values()[index]
            self.widgets['cate_ls'].clear()
            for cate_name in server.cates:
                directory = server.conf[cate_name]
                self.widgets['cate_ls'].append(
                        [cate_name[5:], directory])
            self.widgets['cate_cb'].set_active(0)

    def on_dialog_response(self, dialog, response):
        """
        Create a new download task if uris are provided.
        """
        if response != gtk.RESPONSE_OK:
            dialog.hide()

        task_type = self.widgets['nb'].get_current_page()
        info = {}

        # get server
        server_index = self.widgets['server_cb'].get_active()
        (info['server'], server) = \
                self.main_app.server_group.servers.items()[server_index]
        # get category
        cate_index = self.widgets['cate_cb'].get_active()
        info['cate'] = server.cates[cate_index]
        # task options
        options = dict(self.main_app.conf.default)
        for (pref, widget) in self.prefs.iteritems():
            if pref == 'seed-ratio':
                options[pref] = str(widget.get_value())
            elif hasattr(widget, 'get_value'):
                options[pref] = str(int(widget.get_value()))
            elif hasattr(widget, 'get_text'):
                options[pref] = widget.get_text()
        # clear empty items
        for (pref, value) in options.items():
            if not value:
                del options[pref]
        # bt prioritize
        if self.prefs['bt-prioritize-piece'].get_active():
            options['bt-prioritize-piece'] = 'head,tail'

        if task_type == TASK_METALINK:
            metalink = self.widgets['metalink_file_chooser'].get_filename()
            if metalink and os.path.exists(metalink):
                MetalinkTask(self.main_app, metalink, info, options)
                dialog.hide()
        elif task_type == TASK_NORMAL:
            uris = self.__get_uris(self.widgets['normal_uri_textview'])
            if uris:
                NormalTask(self.main_app, uris, info, options)
                dialog.hide()
        elif task_type == TASK_BT:
            torrent = self.widgets['bt_file_chooser'].get_filename()
            uris = self.__get_uris(self.widgets['bt_uri_textview'])
            if torrent and os.path.exists(torrent):
                BTTask(self.main_app, torrent, uris, info, options)
                dialog.hide()
