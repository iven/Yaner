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
    This file contains the dialogs of Yaner.
"""

import os
import gtk
import uuid

import dbus.service

from Yaner.Server import Server
from Yaner.Category import Category
from Yaner.Constants import *

class TaskDialogMixin:
    """
    This class contains attributes and methods used by task related
    dialogs.
    """

    def __init__(self, glade_file):
        # GTK+ Builder
        builder = gtk.Builder()
        builder.set_translation_domain('yaner')
        builder.add_from_file(glade_file)
        builder.connect_signals(self)
        self.builder = builder
        self.current_options = {}

        self.widgets = {}
        self.prefs = {}

    def update_options(self):
        """
        Update current set task options from the widgets.
        """
        options = self.current_options
        for (pref, widget) in self.get_prefs().iteritems():
            if pref == 'seed-ratio':
                options[pref] = str(widget.get_value())
            elif hasattr(widget, 'get_value'):
                options[pref] = str(int(widget.get_value()))
            elif hasattr(widget, 'get_text'):
                text = widget.get_text()
                if text != '':
                    options[pref] = text
            elif hasattr(widget, 'get_active'):
                if widget.get_active():
                    options[pref] = 'true'
                else:
                    options[pref] = 'false'
        if self.prefs['bt-prioritize-piece'].get_active():
            options['bt-prioritize-piece'] = 'head,tail'
        else:
            options['bt-prioritize-piece'] = ''

    def update_widgets(self):
        """
        Set the status of the widgets in the dialog according to
        current options.
        """
        options = self.current_options
        for (pref, widget) in self.get_prefs().iteritems():
            if hasattr(widget, 'set_value'):
                widget.set_value(float(options[pref]))
            elif hasattr(widget, 'set_text'):
                widget.set_text(options[pref])
            elif hasattr(widget, 'set_active'):
                widget.set_active(options[pref] == 'true')
        if options['bt-prioritize-piece'] == 'head,tail':
            self.get_prefs()['bt-prioritize-piece'].set_active(True)

class TaskNewDialog(TaskDialogMixin, dbus.service.Object):
    """
    This class contains widgets and methods related to new task dialog.
    """

    def __init__(self, main_app):
        TaskDialogMixin.__init__(self, TASK_NEW_UI_FILE)
        dbus.service.Object.__init__(self,
                main_app.bus, TASK_NEW_DIALOG_OBJECT)
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

    def get_prefs(self):
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

    def __set_uris(self, task_type, uris):
        """
        Set URIs of textviews, @uris is a tuple of URIs.
        """
        if task_type == TASK_NORMAL:
            textview = self.widgets['normal_uri_textview']
        elif task_type == TASK_BT:
            textview = self.widgets['bt_uri_textview']
        else:
            return
        tbuffer = textview.get_buffer()
        uris = tbuffer.set_text('\n'.join(uris))

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

    @dbus.service.method(APP_INTERFACE,
            in_signature = 'ia{ss}', out_signature = '')
    def run_dialog(self, task_type, options = None):
        """
        Popup new task dialog.
        """
        widgets = self.__get_widgets()
        # set current page of the notebook
        widgets['nb'].set_current_page(task_type)
        # init widgets status
        self.current_options = dict(self.main_app.conf.task)
        if options:
            self.__set_uris(task_type, options.pop('uris').split('|'))
            for key, value in options.iteritems():
                self.current_options[str(key)] = str(value)
        self.update_widgets()
        # init the server cb
        widgets['server_ls'].clear()
        for server in self.main_app.server_group.get_servers():
            widgets['server_ls'].append([server.get_name(), server.uuid])
        widgets['server_cb'].set_active(0)
        # Show main window
        self.main_app.main_window.present()
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
        self.update_options()
        options = self.current_options
        cate = self.__get_active_cate()
        info = {}
        info['server'] = self.__get_active_server().uuid
        info['cate'] = cate.uuid
        info['uuid'] = str(uuid.uuid4())
        info['percent'] = 0
        info['size'] = 0
        info['gid'] = ''
        info['status'] = 'paused'

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

class TaskProfileDialog(TaskDialogMixin):
    """
    This class contains widgets and methods related to default task profile dialog.
    """
    def __init__(self, main_app):
        TaskDialogMixin.__init__(self, TASK_PROFILE_UI_FILE)
        self.main_app = main_app
    
    def __get_widgets(self):
        """
        Get a dict of widget of preferences dialog.
        """
        if self.widgets == {}:
            builder = self.builder
            widgets = self.widgets
            widgets['dialog'] = builder.get_object("dialog")
            widgets['nb'] = builder.get_object("nb")

        return self.widgets

    def get_prefs(self):
        """
        Get a dict of widget corresponding to a preference in the
        main configuration file.
        """
        if self.prefs == {}:
            builder = self.builder
            prefs = self.prefs
            prefs['split'] = builder.get_object('split_adjustment')
            prefs['max-connection-per-server'] = builder.get_object(
                    'per_server_connections_adjustment')
            prefs['auto-file-renaming'] = builder.get_object(
                    'auto_renaming_checkbutton')
            prefs['connect-timeout'] = builder.get_object(
                    'connect_timeout_adjustment')
            prefs['timeout'] = builder.get_object(
                    'timeout_adjustment')
            prefs['bt-max-open-files'] = builder.get_object(
                    'max_files_adjustment')
            prefs['bt-max-peers'] = builder.get_object(
                    'max_peers_adjustment')
            prefs['bt-tracker-connect-timeout'] = builder.get_object(
                    'tracker_connect_timeout_adjustment')
            prefs['bt-tracker-timeout'] = builder.get_object(
                    'tracker_timeout_adjustment')
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
            prefs['follow-torrent'] = builder.get_object(
                    'follow_torrent_adjustment')
            prefs['follow-metalink'] = builder.get_object(
                    'follow_metalink_adjustment')
        return self.prefs

    def run_dialog(self):
        """
        Popup preferences dialog.
        """
        widgets = self.__get_widgets()
        # init default configuration
        self.current_options = dict(self.main_app.conf.task)
        self.update_widgets()
        # run the dialog
        widgets['dialog'].run()
        
    def on_dialog_response(self, dialog, response):
        """
        Save the options to the config file.
        """
        if response == gtk.RESPONSE_OK:
            self.current_options = {}
            self.update_options()
            for (key, value) in self.current_options.iteritems():
                self.main_app.conf.task[key] = value
        dialog.hide()

