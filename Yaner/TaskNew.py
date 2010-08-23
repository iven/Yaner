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
import uuid

from Yaner.Server import Server
from Yaner.Category import Category
from Yaner.Constants import *

class TaskNew:
    """
    This class contains widgets and methods related to new task dialog.
    """
    def __init__(self, main_app):
        # GTK+ Builder
        builder = gtk.Builder()
        builder.set_translation_domain('yaner')
        builder.add_from_file(TASK_NEW_UI_FILE)
        builder.connect_signals(self)
        self.builder = builder

        self.widgets = {}
        self.prefs = {}
        self.__init_filefilters()

        self.main_app = main_app
    
    def __init_filefilters(self):
        """
        Init Filefilters.
        """
        torrent_filefilter = self.builder.get_object("torrent_filefilter")
        metalink_filefilter = self.builder.get_object("metalink_filefilter")
        torrent_filefilter.add_mime_type("application/x-bittorrent")
        metalink_filefilter.add_mime_type("application/xml")

    def __get_widgets(self):
        """
        Get a dict of widget of new task dialog.
        """
        if self.widgets == {}:
            builder = self.builder
            widgets = self.widgets
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
        return self.widgets

    def __get_prefs(self):
        """
        Get a dict of widget corresponding to a preference in the
        configuration file of new task dialog.
        """
        if self.prefs == {}:
            builder = self.builder
            prefs = self.prefs
            prefs['dir'] = builder.get_object("dir_entry")
            prefs['out'] = builder.get_object("rename_entry")
            prefs['referer'] = builder.get_object("referer_entry")
            prefs['http-user'] = builder.get_object("http_user_entry")
            prefs['http-passwd'] = builder.get_object("http_pass_entry")
            prefs['ftp-user'] = builder.get_object("ftp_user_entry")
            prefs['ftp-passwd'] = builder.get_object("ftp_pass_entry")
            prefs['split'] = builder.get_object('split_adjustment')
            prefs['bt-max-open-files'] = builder.get_object(
                    'max_files_adjustment')
            prefs['bt-max-peers'] = builder.get_object(
                    'max_peers_adjustment')
            prefs['seed-time'] = builder.get_object(
                    'seed_time_adjustment')
            prefs['seed-ratio'] = builder.get_object(
                    'seed_ratio_adjustment')
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
        return self.prefs

    def __get_active_server(self):
        """
        Get current selected Server.
        """
        active_iter = self.widgets['server_cb'].get_active_iter()
        if active_iter != None:
            server_uuid = self.widgets['server_ls'].get(active_iter, 1)[0]
            return Server.instances[server_uuid]
        else:
            return None

    def __get_active_cate(self):
        """
        Get current selected Category.
        """
        active_iter = self.widgets['cate_cb'].get_active_iter()
        if active_iter != None:
            cate_uuid = self.widgets['cate_ls'].get(active_iter, 1)[0]
            return Category.instances[cate_uuid]
        else:
            return None

    def __get_options(self):
        """
        Get current set task options.
        """
        options = self.main_app.get_default_options()
        for (pref, widget) in self.__get_prefs().iteritems():
            if pref == 'seed-ratio':
                options[pref] = str(widget.get_value())
            elif hasattr(widget, 'get_value'):
                options[pref] = str(int(widget.get_value()))
            elif hasattr(widget, 'get_text'):
                text = widget.get_text()
                if text != '':
                    options[pref] = text
        if self.prefs['bt-prioritize-piece'].get_active():
            options['bt-prioritize-piece'] = 'head,tail'
        return options

    def __get_uris(self, task_type):
        """
        Get URIs from textviews, returning a tuple of URIs.
        """
        if task_type == TASK_NORMAL:
            textview = self.widgets['normal_uri_textview']
        elif task_type == TASK_BT:
            textview = self.widgets['bt_uri_textview']
        else:
            return ""
        tbuffer = textview.get_buffer()
        uris = tbuffer.get_text(
                tbuffer.get_start_iter(),
                tbuffer.get_end_iter()
                )
        return [uri.strip() for uri in uris.split("\n") if uri.strip()]

    def __get_metadata_file(self, task_type):
        """
        Get metadata file for BT and Metalink tasks.
        """
        if task_type == TASK_METALINK:
            metadata_file = self.widgets['metalink_file_chooser'].get_filename()
        elif task_type == TASK_BT:
            metadata_file = self.widgets['bt_file_chooser'].get_filename()
        else:
            return ""

        if os.path.exists(metadata_file):
            return metadata_file
        else:
            return ""

    def run_dialog(self, action):
        """
        Popup new task dialog.
        """
        widgets = self.__get_widgets()
        default_conf = self.main_app.get_default_options()
        # set current page of the notebook
        actions = (
                "task_new_normal_action",
                "task_new_bt_action",
                "task_new_metalink_action",
                )
        page = actions.index(action.get_property('name'))
        widgets['nb'].set_current_page(page)
        # init default configuration
        for (pref, widget) in self.__get_prefs().iteritems():
            if hasattr(widget, 'set_value'):
                widget.set_value(float(default_conf[pref]))
            elif hasattr(widget, 'set_text'):
                widget.set_text(default_conf[pref])
        # init the server cb
        widgets['server_ls'].clear()
        for server in self.main_app.server_group.get_servers():
            widgets['server_ls'].append([server.get_name(), server.uuid])
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
        active_cate = self.__get_active_cate()
        if active_cate != None:
            self.prefs['dir'].set_text(active_cate.get_dir())

    def on_server_cb_changed(self, server_cb):
        """
        When server combobox selection changed, update the category combobox.
        """
        active_server = self.__get_active_server()
        if active_server != None:
            self.widgets['cate_ls'].clear()
            for cate in active_server.get_cates():
                self.widgets['cate_ls'].append([cate.get_name(), cate.uuid])
            self.widgets['cate_cb'].set_active(0)

    def on_dialog_response(self, dialog, response):
        """
        Create a new download task if uris are provided.
        """
        if response != gtk.RESPONSE_OK:
            dialog.hide()
            return

        task_type = self.widgets['nb'].get_current_page()
        uris = self.__get_uris(task_type)
        metadata_file = self.__get_metadata_file(task_type)
        options = self.__get_options()
        cate = self.__get_active_cate()
        info = {}
        info['server'] = self.__get_active_server().uuid
        info['cate'] = cate.uuid
        info['uuid'] = str(uuid.uuid1())
        info['percent'] = 0
        info['size'] = 0
        info['gid'] = ''

        if task_type == TASK_METALINK and metadata_file:
            info['metalink'] = metadata_file
            info['type'] = TASK_METALINK
            info['name'] = os.path.basename(metadata_file)
        elif task_type == TASK_NORMAL and uris:
            info['uris'] = '|'.join(uris)
            info['type'] = TASK_NORMAL
            if options.has_key('out'):
                info['name'] = options['out']
            else:
                info['name'] = os.path.basename(uris[0])
        elif task_type == TASK_BT and metadata_file:
            info['torrent'] = metadata_file
            info['uris'] = '|'.join(uris)
            info['type'] = TASK_BT
            info['name'] = os.path.basename(metadata_file)
        else:
            return
        cate.add_task(info, options)
        dialog.hide()

