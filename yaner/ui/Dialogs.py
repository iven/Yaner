#!/usr/bin/env python
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

import os
import xmlrpc.client

from gi.repository import Gtk
from gi.repository import GObject

from yaner import SQLSession
from yaner.Pool import Pool
from yaner.Task import Task, NormalTask, BTTask, MLTask
from yaner.Presentable import Category
from yaner.ui.Misc import load_ui_file
from yaner.utils.Logging import LoggingMixin
from yaner.utils.Configuration import ConfigParser

class TaskDialogMixin(LoggingMixin):
    """
    This class contains attributes and methods used by task related
    dialogs.
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
            TaskDialogMixin._CONFIG = ConfigParser(self._CONFIG_FILE)
        return TaskDialogMixin._CONFIG

    @property
    def builder(self):
        """Get the UI builder of the dialog."""
        if self._builder is None:
            builder = Gtk.Builder()
            builder.set_translation_domain('yaner')
            builder.add_from_file(self._UI_FILE)
            builder.connect_signals(self)
            self._builder = builder
        return self._builder

    @property
    def option_widgets(self):
        """Map task option names to widgets."""
        if self._option_widgets == {}:
            for (option, widget_name) in self._option_widget_names.items():
                self._option_widgets[option] = self.widgets[widget_name]
        return self._option_widgets

    @property
    def options(self):
        """
        Get the current options of the dialog.
        """
        options = self._options

        for (option, widget) in self.option_widgets.items():
            if option == 'seed-ratio':
                options[option] = str(widget.get_value())
            elif hasattr(widget, 'get_value'):
                options[option] = str(int(widget.get_value()))
            elif hasattr(widget, 'get_text'):
                options[option] = widget.get_text().strip()
            elif hasattr(widget, 'get_active'):
                options[option] = 'true' if widget.get_active() else 'false'

        if self.option_widgets['bt-prioritize-piece'].get_active():
            options['bt-prioritize-piece'] = 'head,tail'
        else:
            options['bt-prioritize-piece'] = ''

        return options

    def init_options(self, new_options):
        """
        Reset options and widgets to default. If new_options is provided,
        current options will be updated with it.
        """
        self._options = dict(self.config['new'])
        options = self._options
        if new_options:
            for key, value in new_options.items():
                options[str(key)] = str(value)
        self.update_widgets()

    def update_widgets(self):
        """
        Set the status of the widgets in the dialog according to
        current options.
        """
        options = self._options
        for (option, widget) in self.option_widgets.items():
            if hasattr(widget, 'set_value'):
                widget.set_value(float(options[option]))
            elif hasattr(widget, 'set_text'):
                widget.set_text(options[option])
            elif hasattr(widget, 'set_active'):
                widget.set_active(options[option] == 'true')
        if options['bt-prioritize-piece'] == 'head,tail':
            self.option_widgets['bt-prioritize-piece'].set_active(True)

class TaskNewDialog(TaskDialogMixin):
    """
    This class contains widgets and methods related to new task dialog.
    """

    _UI_FILE = load_ui_file('task_new.ui')
    """The Glade UI file of this dialog."""

    _WIDGET_NAMES = (
            'dialog', 'pool_cb', 'prioritize_checkbutton',
            'normal_uri_textview', 'bt_uri_textview',
            'http_pass_entry', 'ftp_user_entry', 'ftp_pass_entry',
            'torrent_filefilter', 'metalink_filefilter', 'dir_entry',
            'rename_entry', 'language_entry', 'http_user_entry', 'nb',
            'max_peers_adjustment', 'seed_time_adjustment', 'category_cb',
            'seed_ratio_adjustment', 'version_adjustment',
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

    def __init__(self):
        TaskDialogMixin.__init__(self, self._UI_FILE, self._OPTION_DICT)

        self._widgets = {}

        self._init_filefilters()

    @property
    def widgets(self):
        """Get a dict of widget of new task dialog."""
        if self._widgets == {}:
            get_object = self.builder.get_object
            for name in self._WIDGET_NAMES:
                self._widgets[name] = get_object(name)

            self._init_liststores(self._widgets)
        return self._widgets

    @property
    def task_type(self):
        """Get the current task type of the dialog."""
        return self.widgets['nb'].get_current_page()

    @task_type.setter
    def task_type(self, new_type):
        """Set the current task type of the dialog."""
        self.widgets['nb'].set_current_page(new_type)

    @property
    def active_pool(self):
        """Get current selected pool."""
        active_iter = self.widgets['pool_cb'].get_active_iter()
        if active_iter is not None:
            return self.widgets['pool_ls'].get_value(active_iter, 1)
        else:
            return None

    @property
    def active_category(self):
        """Get current selected Category."""
        active_iter = self.widgets['category_cb'].get_active_iter()
        if active_iter is not None:
            return self.widgets['category_ls'].get_value(active_iter, 1)
        else:
            return None

    @property
    def uris(self):
        """Get URIs from textviews, returning a tuple of URIs."""
        if self.task_type == Task.TYPES.NORMAL:
            textview = self.widgets['normal_uri_textview']
        elif self.task_type == Task.TYPES.BT:
            textview = self.widgets['bt_uri_textview']
        else:
            return []
        tbuffer = textview.get_buffer()
        uris = tbuffer.get_text(
                tbuffer.get_start_iter(),
                tbuffer.get_end_iter(),
                False
                )
        return uris.split()

    @uris.setter
    def uris(self, new_uris):
        """
        Set URIs of textviews.
        @type new_uris: C{tuple} or C{list}
        """
        if self.task_type == Task.TYPES.NORMAL:
            textview = self.widgets['normal_uri_textview']
        elif self.task_type == Task.TYPES.BT:
            textview = self.widgets['bt_uri_textview']
        else:
            return
        tbuffer = textview.get_buffer()
        tbuffer.set_text('\n'.join(new_uris))

    @property
    def metadata_file(self):
        """Get metadata file for BT and Metalink tasks."""
        task_type = self.task_type
        if task_type == Task.TYPES.ML:
            metadata_file = self.widgets['metalink_file_chooser'].get_filename()
        elif task_type == Task.TYPES.BT:
            metadata_file = self.widgets['bt_file_chooser'].get_filename()
        else:
            return ""

        if (not metadata_file is None) and os.path.exists(metadata_file):
            return metadata_file
        else:
            return ""

    def _init_filefilters(self):
        """Init Filefilters."""
        torrent_filefilter = self.widgets['torrent_filefilter']
        metalink_filefilter = self.widgets['metalink_filefilter']
        torrent_filefilter.add_mime_type("application/x-bittorrent")
        metalink_filefilter.add_mime_type("application/xml")

    def _init_liststores(self, widgets):
        """Init ListStores."""
        widgets['pool_ls'] = Gtk.ListStore(
                GObject.TYPE_STRING,
                Pool,
                )
        widgets['pool_cb'].set_model(widgets['pool_ls'])

        widgets['category_ls'] = Gtk.ListStore(
                GObject.TYPE_STRING,
                Category,
                )
        widgets['category_cb'].set_model(widgets['category_ls'])

    def run_dialog(self, task_type, options = {}):
        """
        Popup new task dialog.
        """
        widgets = self.widgets
        # set current page of the notebook
        self.task_type = task_type
        # set uri textview
        self.uris = eval(options.pop('uris', '()'))
        # init widgets status
        self.init_options(options)
        # init the server cb
        widgets['pool_ls'].clear()
        for pool in SQLSession.query(Pool):
            widgets['pool_ls'].append([pool.name, pool])
        widgets['pool_cb'].set_active(0)
        # TODO: Show main window
        # run the dialog
        widgets['dialog'].run()

    def on_dir_chooser_button_clicked(self, button):
        """
        When directory chooser button clicked, popup the dialog, and update
        the directory entry.
        """
        dialog = Gtk.FileChooserDialog(_('Select download directory'),
                self.widgets['dialog'],
                Gtk.FileChooserAction.SELECT_FOLDER,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        if dialog.run() == Gtk.ResponseType.OK:
            directory = dialog.get_filename()
            self.widgets['dir_entry'].set_text(directory)
        dialog.destroy()

    def on_category_cb_changed(self, category_cb):
        """
        When category combobox selection changed, update the directory entry.
        """
        if self.active_category is not None:
            self.widgets['dir_entry'].set_text(self.active_category.directory)

    def on_pool_cb_changed(self, pool_cb):
        """
        When server combobox selection changed, update the category combobox.
        """
        if self.active_pool is not None:
            self.widgets['category_ls'].clear()
            for category in self.active_pool.categories:
                self.widgets['category_ls'].append([category.name, category])
            self.widgets['category_cb'].set_active(0)

    def on_dialog_response(self, dialog, response):
        """
        Create a new download task if uris are provided.
        """
        if response != Gtk.ResponseType.OK:
            dialog.hide()
            return

        task_type = self.task_type
        uris = self.uris
        metadata_file = self.metadata_file
        options = self.options

        if task_type == Task.TYPES.NORMAL and uris:
            name = options['out'] if options['out'] else \
                    os.path.basename(uris[0])
            metafile = None
        elif task_type != Task.TYPES.NORMAL and metadata_file:
            name = os.path.basename(metadata_file)
            with open(metadata_file, 'br') as m_file:
                metafile = xmlrpc.client.Binary(m_file.read())
        else:
            return

        TaskClasses = (NormalTask, BTTask, MLTask)

        task = TaskClasses[task_type](name=name, type=task_type,
                metafile=metafile, uris=uris, options=options,
                category=self.active_category, pool=self.active_pool)
        task.start()
        task.pool.queuing.emit('task-added', task)
        dialog.hide()

class TaskProfileDialog(TaskDialogMixin):
    """
    This class contains widgets and methods related to default task profile dialog.
    """

    _UI_FILE = load_ui_file('task_profile.ui')
    """The Glade UI file of this dialog."""

    def __init__(self, main_app):
        TaskDialogMixin.__init__(self, self._UI_FILE)
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
        if response == Gtk.ResponseType.OK:
            self._options = {}
            self.update_options()
            for (key, value) in self._options.items():
                self.main_app.conf.task[key] = value
        dialog.hide()

