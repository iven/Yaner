#!/usr/bin/env python2
# vim:fileencoding=UTF-8

# This file is part of Yaner.

# Yaner - GTK+ interface for aria2 download mananger
# Copyright (C) 2010-2011  Iven <ivenvd#gmail.com>
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
This module contains the dialog classes of L{yaner}.
"""

import gtk
import os
import dbus.service

from yaner.Pool import Pool
from yaner.Constants import U_CONFIG_DIR
from yaner.Constants import BUS_NAME as INTERFACE_NAME
from yaner.ui.Constants import UI_DIR
from yaner.utils.Logging import LoggingMixin
from yaner.utils.Configuration import ConfigParser

class TaskDialogMixin(LoggingMixin):
    """
    This class contains attributes and methods used by task related
    dialogs.
    """

    _CONFIG_DIR = U_CONFIG_DIR
    """
    User config directory containing configuration files and log files.
    """

    _CONFIG_FILE = 'task.conf'
    """The configuration file of the default task options."""

    _CONFIG = None
    """The configuration parser of the default task options."""

    def __init__(self, glade_file, option_widget_names):
        LoggingMixin.__init__(self)

        self._glade_file = glade_file
        self._option_widget_names = option_widget_names
        self._builder = None
        self._options = None
        self._option_widgets = {}

    @property
    def config(self):
        """
        Get the default configuration of task options.
        If the file doesn't exist, read from the default configuration.
        """
        if TaskDialogMixin._CONFIG is None:
            config = ConfigParser(self._CONFIG_DIR, self._CONFIG_FILE)
            if config.empty():
                self.logger.info(_('No task options config file, creating...'))
                from yaner.Configurations import TASK_CONFIG
                config.update({'options': TASK_CONFIG['options'].copy()})
            TaskDialogMixin._CONFIG = config
        return TaskDialogMixin._CONFIG

    @property
    def builder(self):
        """Get the UI builder of the dialog."""
        if self._builder is None:
            builder = gtk.Builder()
            builder.set_translation_domain('yaner')
            builder.add_from_file(self._UI_FILE)
            builder.connect_signals(self)
            self._builder = builder
        return self._builder

    @property
    def option_widgets(self):
        """Map task option names to widgets."""
        if self._option_widgets == {}:
            for (option, widget_name) in self._option_widget_names.iteritems():
                self._option_widgets[option] = self.widgets[widget_name]
        return self._option_widgets

    @property
    def options(self):
        """
        Get the current options of the dialog.
        """
        options = self._options
        for (option, widget) in self.option_widgets.iteritems():
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
        if self.option_widgets['bt-prioritize-piece'].get_active():
            options['bt-prioritize-piece'] = 'head,tail'
        else:
            options['bt-prioritize-piece'] = ''
        return options

    def init_options(self, new_options={}):
        """
        Reset options and widgets to default. If new_options is provided,
        current options will be updated with it.
        """
        self._options = self.config['options'].copy()
        options = self._options
        if new_options:
            self.uris = new_options.pop('uris').split('|')
            for key, value in new_options.iteritems():
                options[str(key)] = str(value)
        self.update_widgets()

    def update_widgets(self):
        """
        Set the status of the widgets in the dialog according to
        current options.
        """
        options = self._options
        for (pref, widget) in self.option_widgets.iteritems():
            if hasattr(widget, 'set_value'):
                widget.set_value(float(options[pref]))
            elif hasattr(widget, 'set_text'):
                widget.set_text(options[pref])
            elif hasattr(widget, 'set_active'):
                widget.set_active(options[pref] == 'true')
        if options['bt-prioritize-piece'] == 'head,tail':
            self.option_widgets['bt-prioritize-piece'].set_active(True)

class TaskNewDialog(TaskDialogMixin, dbus.service.Object):
    """
    This class contains widgets and methods related to new task dialog.
    """

    _OBJECT_NAME = '/task_new_dialog'
    """DBus object name of the dialog."""

    _UI_FILE = os.path.join(UI_DIR, "task_new.ui")
    """The Glade UI file of this dialog."""

    _WIDGET_NAMES = (
            'dialog', 'server_cb', 'prioritize_checkbutton',
            'cate_ls', 'normal_uri_textview', 'bt_uri_textview',
            'http_pass_entry', 'ftp_user_entry', 'ftp_pass_entry',
            'torrent_filefilter', 'metalink_filefilter', 'dir_entry',
            'rename_entry', 'language_entry', 'http_user_entry', 'nb',
            'max_peers_adjustment', 'seed_time_adjustment', 'cate_cb',
            'seed_ratio_adjustment', 'version_adjustment', 'server_ls',
            'bt_file_chooser', 'metalink_file_chooser', 'os_adjustment',
            'split_adjustment', 'max_files_adjustment', 'referer_entry',
            'servers_adjustment', 'location_entry'
            )
    """All widgets in the glade file."""

    _OPTION_DICT = {
            'dir': 'dir_entry',
            'out': 'rename_entry',
            'referer': 'referer_entry',
            'http-user': 'http_user_entry',
            'http-passwd': 'http_pass_entry',
            'ftp-user': 'ftp_user_entry',
            'ftp-passwd': 'ftp_pass_entry',
            'split': 'split_adjustment',
            'bt-max-open-files': 'max_files_adjustment',
            'bt-max-peers': 'max_peers_adjustment',
            'seed-time': 'seed_time_adjustment',
            'seed-ratio': 'seed_ratio_adjustment',
            'bt-prioritize-piece': 'prioritize_checkbutton',
            'metalink-servers': 'servers_adjustment',
            'metalink-location': 'location_entry',
            'metalink-language': 'language_entry',
            'metalink-os': 'os_adjustment',
            'metalink-version': 'version_adjustment',
            }
    """Map task option names to widget names."""

    def __init__(self, bus, pool_model):
        TaskDialogMixin.__init__(self, self._UI_FILE, self._OPTION_DICT)
        dbus.service.Object.__init__(self, bus, self._OBJECT_NAME)

        self._widgets = {}
        self._pool_model = pool_model

        self._init_filefilters()

    @property
    def widgets(self):
        """Get a dict of widget of new task dialog."""
        if self._widgets == {}:
            get_object = self.builder.get_object
            for name in self._WIDGET_NAMES:
                self._widgets[name] = get_object(name)
        return self._widgets

    def _init_filefilters(self):
        """
        Init Filefilters.
        """
        torrent_filefilter = self.widgets['torrent_filefilter']
        metalink_filefilter = self.widgets['metalink_filefilter']
        torrent_filefilter.add_mime_type("application/x-bittorrent")
        metalink_filefilter.add_mime_type("application/xml")

    def __get_active_server(self):
        """
        Get current selected Server.
        """
        active_iter = self.widgets['server_cb'].get_active_iter()
        if active_iter is not None:
            server_uuid = self.widgets['server_ls'].get(active_iter, 1)[0]
            return Server.instances[server_uuid]
        else:
            return None

    def __get_active_cate(self):
        """
        Get current selected Category.
        """
        active_iter = self.widgets['cate_cb'].get_active_iter()
        if active_iter is not None:
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

    @dbus.service.method(INTERFACE_NAME,
            in_signature = 'ia{ss}', out_signature = '')
    def run_dialog(self, task_type, options = {}):
        """
        Popup new task dialog.
        """
        widgets = self.widgets
        # set current page of the notebook
        widgets['nb'].set_current_page(task_type)
        # init widgets status
        self.init_options(options)
        # init the server cb
        widgets['server_ls'].clear()
        #for pool in self._pools:
        #    widgets['server_ls'].append([pool.name, pool])
        #widgets['server_cb'].set_active(0)
        # TODO: Show main window
        # run the dialog
        widgets['dialog'].run()
        
    def on_dir_chooser_button_clicked(self, button):
        """
        When directory chooser button clicked, popup the dialog, and update
        the directory entry.
        """
        dialog = gtk.FileChooserDialog(_('Select download directory'),
                self.widgets['dialog'],
                gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                (_('_Cancel'), gtk.RESPONSE_CANCEL,
                    _('_Select'), gtk.RESPONSE_OK))
        if dialog.run() == gtk.RESPONSE_OK:
            directory = dialog.get_filename()
            self.widgets['dir_entry'].set_text(directory)
        dialog.destroy()

    def on_cate_cb_changed(self, cate_cb):
        """
        When category combobox selection changed, update the directory entry.
        """
        active_cate = self.__get_active_cate()
        if active_cate is not None:
            self.prefs['dir'].set_text(active_cate.get_dir())

    def on_server_cb_changed(self, server_cb):
        """
        When server combobox selection changed, update the category combobox.
        """
        active_server = self.__get_active_server()
        if active_server is not None:
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
        options = self._options
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
        self._options = dict(self.main_app.conf.task)
        self.update_widgets()
        # run the dialog
        widgets['dialog'].run()

    def on_dialog_response(self, dialog, response):
        """
        Save the options to the config file.
        """
        if response == gtk.RESPONSE_OK:
            self._options = {}
            self.update_options()
            for (key, value) in self._options.iteritems():
                self.main_app.conf.task[key] = value
        dialog.hide()

