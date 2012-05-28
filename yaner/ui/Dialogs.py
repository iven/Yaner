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

from gi.repository import Gtk, Gio
from gi.repository.Gio import SettingsBindFlags as BindFlags

from yaner.Task import Task
from yaner.ui.Widgets import LeftAlignedLabel, AlignedExpander, URIsView
from yaner.ui.Widgets import MetafileChooserButton, FileChooserEntry
from yaner.ui.Widgets import HORIZONTAL, VERTICAL, Box
from yaner.ui.PoolTree import PoolModel
from yaner.ui.CategoryComboBox import CategoryFilterModel, CategoryComboBox
from yaner.utils.Logging import LoggingMixin

_BT_FILTER_NAME = _('Torrent Files')
_ML_FILTER_NAME = _('Metalink Files')
_BT_MIME_TYPES = {'application/x-bittorrent'}
_ML_MIME_TYPES = {'application/metalink4+xml', 'application/metalink+xml'}
_RESPONSE_RESET = -1
_RESPONSE_SAVE = -2

class _TaskOption(object):
    """An widget wrapper for convert between aria2c needed format and widget
    values.
    """
    def __init__(self, widget, property_, mapper):
        self.widget = widget
        self.property_ = property_
        self.mapper = mapper

    @property
    def value(self):
        """Value for used in XML-RPC."""
        widget_value = self.widget.get_property(self.property_)
        return self.mapper(widget_value)

    @property
    def widget_value(self):
        """Get the value of the widget."""
        return self.widget.get_property(self.property_)

    @widget_value.setter
    def widget_value(self, value):
        """Set the value of the widget."""
        self.widget.set_property(self.property_, value)

    ## Mappers
    default_mapper = lambda x: x
    string_mapper = lambda x: x
    bool_mapper = lambda x: 'true' if x else 'false'
    int_mapper = lambda x: str(int(x))
    float_mapper = lambda x: str(float(x))
    kib_mapper = lambda x: str(int(x) * 1024)
    mib_mapper = lambda x: str(int(x) * 1024 * 1024)
    prioritize_mapper = lambda x: 'head, tail' if x else ''

class _TaskNewUI(LoggingMixin):
    """Base class for the UIs of the new task dialog."""

    def __init__(self, task_options, expander_label):
        LoggingMixin.__init__(self)

        self.settings = Gio.Settings('com.kissuki.yaner.task')
        # Don't apply changes to dconf until apply() is called
        self.settings.delay()

        self._task_options = task_options.copy()

        expander = AlignedExpander(expander_label)
        self._uris_expander = expander

        vbox = Box(VERTICAL)
        expander.add(vbox)
        self._content_box = vbox

    @property
    def uris_expander(self):
        return self._uris_expander

    @property
    def aria2_options(self):
        return {key: option.value for (key, option) in self._task_options.items()}

    def activate(self, new_options):
        """When the UI changed to this one, bind and update the setting widgets."""
        keys = self.settings.list_keys()
        for key, option in self._task_options.items():
            if key in keys:
                self.settings.bind(key,
                                   option.widget,
                                   option.property_,
                                   BindFlags.DEFAULT
                                  )
            try:
                option.widget_value = new_options[key]
            except KeyError:
                pass
        self._uris_expander.show_all()

    def deactivate(self):
        """When the UI changed from this one, unbind the properties."""
        self.settings.revert()

    def response(self, response_id):
        """When dialog responsed, create new task. Returning if the dialog should
        be kept showing.
        """
        settings = self.settings

        if response_id in (Gtk.ResponseType.CANCEL, Gtk.ResponseType.DELETE_EVENT):
            return False
        elif response_id == _RESPONSE_RESET:
            task_options = self._task_options
            keys = self.settings.list_keys()
            for key, option in task_options.items():
                if key in keys:
                    settings.reset(key)
                    # When in delayed writing mode, widget values doesn't update
                    # when the settings isn't different with the default value,
                    # so update it manually
                    option.widget_value = settings.get_value(key).unpack()
            settings.apply()
            return True
        elif response_id == _RESPONSE_SAVE:
            settings.apply()
            return True
        else:
            return True

class _TaskNewDefaultUI(_TaskNewUI):
    """Default UI of the new task dialog."""
    def __init__(self, task_options, parent):
        _TaskNewUI.__init__(self, task_options,
                            expander_label= _('<b>URIs/Torrent/Metalink File</b>')
                           )

        box = self._content_box

        text = _('Select Torrent/Metalink Files')
        entry = FileChooserEntry(text,
                                 parent,
                                 Gtk.FileChooserAction.OPEN,
                                 update_entry=False,
                                 mime_list=(
                                     (_BT_FILTER_NAME, _BT_MIME_TYPES),
                                     (_ML_FILTER_NAME, _ML_MIME_TYPES),
                                 ),
                                 truncate_multiline=True,
                                 secondary_icon_tooltip_text=text
                                )
        entry.set_size_request(350, -1)
        box.pack_start(entry)
        self._task_options['uris'] = _TaskOption(entry, 'text',
                                                 _TaskOption.string_mapper)

        self.uri_entry = entry

    def activate(self, options):
        _TaskNewUI.activate(self, options)
        self.uri_entry.grab_focus()

class _TaskNewNormalUI(_TaskNewUI):
    """Normal UI of the new task dialog."""
    def __init__(self, task_options):
        _TaskNewUI.__init__(self, task_options,
                            expander_label=_('<b>Mirrors</b> - one or more URI(s) for <b>one</b> task')
                           )

        box = self._content_box

        uris_view = URIsView()
        uris_view.set_size_request(350, 70)
        box.pack_start(uris_view)
        self._task_options['uris'] = _TaskOption(uris_view, 'uris',
                                                 _TaskOption.default_mapper)

        hbox = Box(HORIZONTAL)
        box.pack_start(hbox)

        # Rename
        label = LeftAlignedLabel(_('Rename:'))
        hbox.pack_start(label, expand=False)

        entry = Gtk.Entry(activates_default=True)
        hbox.pack_start(entry)
        self._task_options['out'] = _TaskOption(entry, 'text',
                                                _TaskOption.string_mapper)

        # Connections
        label = LeftAlignedLabel(_('Connections:'))
        hbox.pack_start(label, expand=False)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        hbox.pack_start(spin_button)
        self._task_options['split'] = _TaskOption(spin_button, 'value',
                                                  _TaskOption.int_mapper)

        self._uris_view = uris_view

    @property
    def uris_view(self):
        return self._uris_view

    def activate(self, options):
        _TaskNewUI.activate(self, options)
        self._uris_view.grab_focus()

    def response(self, response_id):
        if response_id == Gtk.ResponseType.OK:
            options = self.aria2_options

            # Workaround for aria2 bug#3527521
            options.pop('bt-prioritize-piece')

            category = options.pop('category')
            uris = options.pop('uris')
            if not uris:
                return True

            name = options['out'] if options['out'] else os.path.basename(uris[0])

            Task(name=name, uris=uris, options=options, category=category).start()

            return False
        else:
            return _TaskNewUI.response(self, response_id)

class _TaskNewBTUI(_TaskNewUI):
    """BT UI of the new task dialog."""
    def __init__(self, task_options):
        _TaskNewUI.__init__(self, task_options,
                            expander_label=_('<b>Torrent File</b>')
                           )

        box = self._content_box

        button = MetafileChooserButton(title=_('Select torrent file'),
                                       mime_types=_BT_MIME_TYPES,
                                      )
        button.set_size_request(350, -1)
        box.pack_start(button)
        self._task_options['torrent_filename'] = _TaskOption(
            button, 'filename', _TaskOption.string_mapper)

    def response(self, response_id):
        if response_id == Gtk.ResponseType.OK:
            options = self.aria2_options

            torrent_filename = options.pop('torrent_filename')
            if torrent_filename is None:
                return True
            else:
                name = os.path.basename(torrent_filename)
                with open(torrent_filename, 'br') as torrent_file:
                    torrent = xmlrpc.client.Binary(torrent_file.read())

            uris = options.pop('uris')
            category = options.pop('category')

            Task(name=name, torrent=torrent, uris=uris,
                 options=options, category=category).start()

            return False
        else:
            return _TaskNewUI.response(self, response_id)

class _TaskNewMLUI(_TaskNewUI):
    """Metalink UI of the new task dialog."""
    def __init__(self, task_options):
        _TaskNewUI.__init__(self, task_options,
                            expander_label=_('<b>Metalink File</b>')
                           )

        box = self._content_box

        button = MetafileChooserButton(title=_('Select metalink file'),
                                       mime_types=_ML_MIME_TYPES,
                                      )
        button.set_size_request(350, -1)
        box.pack_start(button)
        self._task_options['metalink_filename'] = _TaskOption(
            button, 'filename', _TaskOption.string_mapper)

    def response(self, response_id):
        if response_id == Gtk.ResponseType.OK:
            options = self.aria2_options

            # Workaround for aria2 bug#3527521
            options.pop('uris')

            metalink_filename = options.pop('metalink_filename')
            if metalink_filename is None:
                return True
            else:
                name = os.path.basename(metalink_filename)
                with open(metalink_filename, 'br') as metalink_file:
                    metafile = xmlrpc.client.Binary(metalink_file.read())

            category = options.pop('category')

            Task(name=name, metafile=metafile, options=options,
                 category=category).start()
            return False
        else:
            return _TaskNewUI.response(self, response_id)

class TaskNewDialog(Gtk.Dialog, LoggingMixin):
    """Dialog for creating new tasks."""
    def __init__(self, parent, pool_model):
        """"""
        Gtk.Dialog.__init__(self, title=_('New Task'), parent=parent,
                            flags=(Gtk.DialogFlags.DESTROY_WITH_PARENT |
                                   Gtk.DialogFlags.MODAL),
                           )
        LoggingMixin.__init__(self)

        self._ui = None
        self._default_ui = None
        self._normal_ui = None
        self._bt_ui = None
        self._ml_ui = None

        self._task_options = {}

        ### Action Area
        action_area = self.get_action_area()
        action_area.set_layout(Gtk.ButtonBoxStyle.START)

        button = Gtk.Button.new_from_stock(Gtk.STOCK_CANCEL)
        self.add_action_widget(button, Gtk.ResponseType.CANCEL)
        action_area.set_child_secondary(button, True)

        image = Gtk.Image.new_from_stock(Gtk.STOCK_GO_DOWN, Gtk.IconSize.BUTTON)
        button = Gtk.Button(_('_Download'), image=image, use_underline=True)
        self.add_action_widget(button, Gtk.ResponseType.OK)
        action_area.set_child_secondary(button, True)

        advanced_buttons = []

        image = Gtk.Image.new_from_stock(Gtk.STOCK_UNDO, Gtk.IconSize.BUTTON)
        button = Gtk.Button(_('_Reset Settings'), image=image, use_underline=True)
        button.set_no_show_all(True)
        self.add_action_widget(button, _RESPONSE_RESET)
        advanced_buttons.append(button)

        image = Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.BUTTON)
        button = Gtk.Button(_('_Save Settings'), image=image, use_underline=True)
        button.set_no_show_all(True)
        self.add_action_widget(button, _RESPONSE_SAVE)
        advanced_buttons.append(button)

        ### Content Area
        content_area = self.get_content_area()

        vbox = Box(VERTICAL)
        content_area.add(vbox)
        self._main_vbox = vbox

        ## Save to
        expander = AlignedExpander(_('<b>Save to...</b>'))
        expander.connect_after('activate', self.update_size)
        vbox.pack_start(expander)
        self.save_expander = expander

        hbox = Box(HORIZONTAL)
        expander.add(hbox)

        # Directory
        entry = FileChooserEntry(_('Select download directory'),
                                 self,
                                 Gtk.FileChooserAction.SELECT_FOLDER
                                )
        hbox.pack_end(entry)
        self._task_options['dir'] = _TaskOption(
            entry, 'text', _TaskOption.string_mapper)

        model = CategoryFilterModel(pool_model)
        combo_box = CategoryComboBox(model, self)
        combo_box.connect('changed', self._on_category_cb_changed, entry)
        combo_box.set_active(0)
        hbox.pack_start(combo_box)
        self._task_options['category'] = _TaskOption(
            combo_box, 'category', _TaskOption.default_mapper)

        ## Advanced
        expander = AlignedExpander(_('<b>Advanced</b>'), expanded=False)
        expander.connect_after('activate', self._on_advanced_expander_activated, advanced_buttons)
        expander.connect_after('activate', self.update_size)
        vbox.pack_end(expander)
        self.advanced_expander = expander

        notebook = Gtk.Notebook()
        expander.add(notebook)

        ## Normal Task Page
        label = Gtk.Label(_('Normal Task'))
        vbox = Box(VERTICAL, border_width=5)
        notebook.append_page(vbox, label)

        table = Gtk.Table(5, 4, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(table, expand=False)

        # Speed Limit
        label = LeftAlignedLabel(_('Upload Limit(KiB/s):'))
        table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=0, upper=4096, step_increment=10)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 0, 1)
        self._task_options['max-upload-limit'] = _TaskOption(
            spin_button, 'value', _TaskOption.kib_mapper)

        label = LeftAlignedLabel(_('Download Limit(KiB/s):'))
        table.attach_defaults(label, 2, 3, 0, 1)

        adjustment = Gtk.Adjustment(lower=0, upper=4096, step_increment=10)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 0, 1)
        self._task_options['max-download-limit'] = _TaskOption(
            spin_button, 'value', _TaskOption.kib_mapper)

        # Retry
        label = LeftAlignedLabel(_('Max Retries:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=60, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 1, 2)
        self._task_options['max-tries'] = _TaskOption(spin_button, 'value',
                                                      _TaskOption.int_mapper)

        label = LeftAlignedLabel(_('Retry Interval(sec):'))
        table.attach_defaults(label, 2, 3, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=60, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 1, 2)
        self._task_options['retry-wait'] = _TaskOption(spin_button, 'value',
                                                       _TaskOption.int_mapper)

        # Timeout
        label = LeftAlignedLabel(_('Timeout(sec):'))
        table.attach_defaults(label, 0, 1, 2, 3)

        adjustment = Gtk.Adjustment(lower=1, upper=300, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 2, 3)
        self._task_options['timeout'] = _TaskOption(spin_button, 'value',
                                                    _TaskOption.int_mapper)

        label = LeftAlignedLabel(_('Connect Timeout(sec):'))
        table.attach_defaults(label, 2, 3, 2, 3)

        adjustment = Gtk.Adjustment(lower=1, upper=300, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 2, 3)
        self._task_options['connect-timeout'] = _TaskOption(spin_button, 'value',
                                                            _TaskOption.int_mapper)

        # Split and Connections
        label = LeftAlignedLabel(_('Split Size(MiB):'))
        table.attach_defaults(label, 0, 1, 3, 4)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 3, 4)
        self._task_options['min-split-size'] = _TaskOption(spin_button, 'value',
                                                           _TaskOption.mib_mapper)

        label = LeftAlignedLabel(_('Per Server Connections:'))
        table.attach_defaults(label, 2, 3, 3, 4)

        adjustment = Gtk.Adjustment(lower=1, upper=10, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 3, 4)
        self._task_options['max-connection-per-server'] = _TaskOption(
            spin_button, 'value', _TaskOption.int_mapper)

        # Referer
        label = LeftAlignedLabel(_('Referer:'))
        table.attach_defaults(label, 0, 1, 4, 5)

        entry = Gtk.Entry(activates_default=True)
        table.attach_defaults(entry, 1, 4, 4, 5)
        self._task_options['referer'] = _TaskOption(entry, 'text',
                                                    _TaskOption.string_mapper)

        # Header
        label = LeftAlignedLabel(_('HTTP Header:'))
        table.attach_defaults(label, 0, 1, 5, 6)

        entry = Gtk.Entry(activates_default=True)
        table.attach_defaults(entry, 1, 4, 5, 6)
        self._task_options['header'] = _TaskOption(entry, 'text',
                                                   _TaskOption.string_mapper)

        ## BT Task Page
        label = Gtk.Label(_('BitTorrent'))
        vbox = Box(VERTICAL, border_width=5)
        notebook.append_page(vbox, label)

        table = Gtk.Table(4, 4, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(table, expand=False)

        # Limit
        label = LeftAlignedLabel(_('Max open files:'))
        table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 0, 1)
        self._task_options['bt-max-open-files'] = _TaskOption(
            spin_button, 'value', _TaskOption.int_mapper)

        label = LeftAlignedLabel(_('Max peers:'))
        table.attach_defaults(label, 2, 3, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 0, 1)
        self._task_options['bt-max-peers'] = _TaskOption(spin_button, 'value',
                                                         _TaskOption.int_mapper)

        # Seed
        label = LeftAlignedLabel(_('Seed time(min):'))
        table.attach_defaults(label, 0, 1, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=7200, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 1, 2)
        self._task_options['seed-time'] = _TaskOption(spin_button, 'value',
                                                      _TaskOption.int_mapper)

        label = LeftAlignedLabel(_('Seed ratio:'))
        table.attach_defaults(label, 2, 3, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=20, step_increment=.1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True, digits=1)
        table.attach_defaults(spin_button, 3, 4, 1, 2)
        self._task_options['seed-ratio'] = _TaskOption(spin_button, 'value',
                                                       _TaskOption.float_mapper)

        # Timeout
        label = LeftAlignedLabel(_('Timeout(sec):'))
        table.attach_defaults(label, 0, 1, 2, 3)

        adjustment = Gtk.Adjustment(lower=1, upper=300, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 2, 3)
        self._task_options['bt-tracker-timeout'] = _TaskOption(
            spin_button, 'value', _TaskOption.int_mapper)

        label = LeftAlignedLabel(_('Connect Timeout(sec):'))
        table.attach_defaults(label, 2, 3, 2, 3)

        adjustment = Gtk.Adjustment(lower=1, upper=300, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 2, 3)
        self._task_options['bt-tracker-connect-timeout'] = _TaskOption(
            spin_button, 'value', _TaskOption.int_mapper)

        label = LeftAlignedLabel(_('Try to download first and last pieces first'))
        table.attach_defaults(label, 0, 3, 3, 4)
        switch = Gtk.Switch()
        table.attach_defaults(switch, 3, 4, 3, 4)
        self._task_options['bt-prioritize-piece'] = _TaskOption(
            switch, 'active', _TaskOption.prioritize_mapper)

        label = LeftAlignedLabel(_('Convert downloaded torrent files to BitTorrent tasks'))
        table.attach_defaults(label, 0, 3, 4, 5)
        switch = Gtk.Switch()
        table.attach_defaults(switch, 3, 4, 4, 5)
        self._task_options['follow-torrent'] = _TaskOption(switch, 'active',
                                                           _TaskOption.bool_mapper)

        # Mirrors
        expander = AlignedExpander(_('Mirrors'), expanded=False)
        expander.set_tooltip_text(
            _('For single file torrents, a mirror can be a ' \
              'complete URI pointing to the resource or if the mirror ' \
              'ends with /, name in torrent file is added. For ' \
              'multi-file torrents, name and path in torrent are ' \
              'added to form a URI for each file.'))
        expander.connect_after('activate', self.update_size)
        vbox.pack_start(expander, expand=False)

        vbox = Box(VERTICAL)
        expander.add(vbox)

        uris_view = URIsView()
        uris_view.set_size_request(-1, 70)
        vbox.pack_start(uris_view)
        self._task_options['uris'] = _TaskOption(uris_view, 'uris',
                                                 _TaskOption.default_mapper)

        ## Metalink Page
        label = Gtk.Label(_('Metalink'))
        vbox = Box(VERTICAL, border_width=5)
        notebook.append_page(vbox, label)

        table = Gtk.Table(5, 2, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(table, expand=False)

        label = LeftAlignedLabel(_('Download Servers:'))
        table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=64, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 0, 1)
        self._task_options['split'] = _TaskOption(spin_button, 'value',
                                                  _TaskOption.int_mapper)

        label = LeftAlignedLabel(_('Preferred locations:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 1, 2)
        self._task_options['metalink-location'] = _TaskOption(
            entry, 'text', _TaskOption.string_mapper)

        label = LeftAlignedLabel(_('Language:'))
        table.attach_defaults(label, 0, 1, 2, 3)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 2, 3)
        self._task_options['metalink-language'] = _TaskOption(
            entry, 'text', _TaskOption.string_mapper)

        label = LeftAlignedLabel(_('Version:'))
        table.attach_defaults(label, 0, 1, 3, 4)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 3, 4)
        self._task_options['metalink-version'] = _TaskOption(
            entry, 'text', _TaskOption.string_mapper)

        label = LeftAlignedLabel(_('OS:'))
        table.attach_defaults(label, 0, 1, 4, 5)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 4, 5)
        self._task_options['metalink-os'] = _TaskOption(
            entry, 'text', _TaskOption.string_mapper)

        hbox = Box(HORIZONTAL)
        vbox.pack_start(hbox, expand=False)

        label = LeftAlignedLabel(_('Convert downloaded metalink files to Metalink tasks'))
        hbox.pack_start(label)

        switch = Gtk.Switch()
        hbox.pack_start(switch)
        self._task_options['follow-metalink'] = _TaskOption(switch, 'active',
                                                            _TaskOption.bool_mapper)

        ## Miscellaneous Page
        label = Gtk.Label(_('Miscellaneous'))
        vbox = Box(VERTICAL, border_width=5)
        notebook.append_page(vbox, label)

        table = Gtk.Table(2, 4, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(table, expand=False)

        # Overwrite and Rename
        label = LeftAlignedLabel(_('Allow Overwrite:'))
        table.attach_defaults(label, 0, 1, 0, 1)

        switch = Gtk.Switch()
        table.attach_defaults(switch, 1, 2, 0, 1)
        self._task_options['allow-overwrite'] = _TaskOption(switch, 'active',
                                                            _TaskOption.bool_mapper)

        label = LeftAlignedLabel(_('Auto Rename Files:'))
        table.attach_defaults(label, 2, 3, 0, 1)

        switch = Gtk.Switch()
        table.attach_defaults(switch, 3, 4, 0, 1)
        self._task_options['auto-file-renaming'] = _TaskOption(
            switch, 'active', _TaskOption.bool_mapper)

        label = LeftAlignedLabel(_('Proxy:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        entry = Gtk.Entry(activates_default=True)
        entry.set_placeholder_text(_('Format: [http://][USER:PASSWORD@]HOST[:PORT]'))
        table.attach_defaults(entry, 1, 4, 1, 2)
        self._task_options['all-proxy'] = _TaskOption(entry, 'text',
                                                      _TaskOption.string_mapper)

        # Authorization
        expander = AlignedExpander(_('Authorization'), expanded=False)
        expander.connect_after('activate', self.update_size)
        vbox.pack_start(expander, expand=False)

        table = Gtk.Table(2, 4, False, row_spacing=5, column_spacing=5)
        expander.add(table)

        label = LeftAlignedLabel(_('HTTP User:'))
        table.attach_defaults(label, 0, 1, 0, 1)

        entry = Gtk.Entry(activates_default=True)
        table.attach_defaults(entry, 1, 2, 0, 1)
        self._task_options['http-user'] = _TaskOption(entry, 'text',
                                                      _TaskOption.string_mapper)

        label = LeftAlignedLabel(_('Password'))
        table.attach_defaults(label, 2, 3, 0, 1)

        entry = Gtk.Entry(activates_default=True)
        table.attach_defaults(entry, 3, 4, 0, 1)
        self._task_options['http-passwd'] = _TaskOption(entry, 'text',
                                                        _TaskOption.string_mapper)

        label = LeftAlignedLabel(_('FTP User:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        entry = Gtk.Entry(activates_default=True)
        table.attach_defaults(entry, 1, 2, 1, 2)
        self._task_options['ftp-user'] = _TaskOption(entry, 'text',
                                                     _TaskOption.string_mapper)

        label = LeftAlignedLabel(_('Password'))
        table.attach_defaults(label, 2, 3, 1, 2)

        entry = Gtk.Entry(activates_default=True)
        table.attach_defaults(entry, 3, 4, 1, 2)
        self._task_options['ftp-passwd'] = _TaskOption(entry, 'text',
                                                       _TaskOption.string_mapper)

        self.show_all()

    @property
    def default_ui(self):
        """Get the default UI."""
        if self._default_ui is None:
            ui = _TaskNewDefaultUI(self._task_options, self)
            ui.uri_entry.connect('response', self._on_metafile_selected)
            ui.uri_entry.connect('changed', self._on_default_entry_changed)
            self._default_ui = ui
        return self._default_ui

    @property
    def normal_ui(self):
        """Get the normal UI."""
        if self._normal_ui is None:
            ui = _TaskNewNormalUI(self._task_options)
            text_buffer = ui.uris_view.text_buffer
            text_buffer.connect('changed', self._on_normal_uris_view_changed)
            self._normal_ui = ui
        return self._normal_ui

    @property
    def bt_ui(self):
        """Get the BT UI."""
        if self._bt_ui is None:
            self._bt_ui = _TaskNewBTUI(self._task_options)
        return self._bt_ui

    @property
    def ml_ui(self):
        """Get the ML UI."""
        if self._ml_ui is None:
            self._ml_ui = _TaskNewMLUI(self._task_options)
        return self._ml_ui

    def _on_advanced_expander_activated(self, expander, buttons):
        """When advanced button activated, show or hide advanced buttons."""
        for button in buttons:
            if expander.get_expanded():
                button.show()
            else:
                button.hide()

    def _on_category_cb_changed(self, category_cb, entry):
        """When category combo box changed, update the directory entry."""
        iter_ = category_cb.get_active_iter()
        model = category_cb.get_model()
        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)
        entry.set_text(presentable.directory)
        self.logger.debug('Category is changed to {}.'.format(presentable))

    def _on_metafile_selected(self, dialog, response_id):
        """When meta file chooser dialog responsed, switch to torrent or metalink
        mode."""
        if response_id == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            current_filter = dialog.get_filter().get_name()
            if current_filter == _BT_FILTER_NAME:
                self.logger.info(
                    'Torrent file selected, changing to bittorrent UI...')
                self.set_ui(self.bt_ui, {'torrent_filename': filename})
            elif current_filter == _ML_FILTER_NAME:
                self.logger.info(
                    'Metalink file selected, changing to metalink UI...')
                self.set_ui(self.ml_ui, {'metalink_filename': filename})
            else:
                raise RuntimeError('No such filter' + current_filter)

    def _on_default_entry_changed(self, entry):
        """When the entry in the default content box changed, switch to normal
        mode."""
        # When default UI activated, the entry text is cleared, we should
        # ignore this.
        if self._ui is not self.normal_ui:
            self.logger.info('URIs inputed, changing to normal UI...')
            self.set_ui(self.normal_ui, {'uris': entry.get_text()})

    def _on_normal_uris_view_changed(self, text_buffer):
        """When the uris view in the normal UI cleared, switch to default mode."""
        if text_buffer.get_property('text') == '':
            self.logger.info('URIs cleared, changing to default UI...')
            self.set_ui(self.default_ui, {'uris': ''})
        elif self._ui is not self.normal_ui:
            # When it's already the normal UI, and the text of the
            # URIs view is set (from the browser), the textview will
            # firstly been cleared, and it changes to default UI,
            # in this case we need to set the UI back to normal UI.
            self.set_ui(self.normal_ui, {})

    def do_response(self, response_id):
        """Create a new download task if uris are provided."""
        if not self._ui.response(response_id):
            self.hide()

    def set_ui(self, new_ui, options=None):
        """Set the UI of the dialog."""
        # Remove current child of uris_expander
        if self._ui is not new_ui:
            main_vbox = self._main_vbox
            if self._ui is not None:
                main_vbox.remove(self._ui.uris_expander)
            main_vbox.pack_start(new_ui.uris_expander)
            main_vbox.reorder_child(new_ui.uris_expander, 0)

        if new_ui is self.default_ui:
            # Hide the advanced buttons when changing to default UI
            if self.advanced_expander.get_expanded():
                self.advanced_expander.emit('activate')
            self.advanced_expander.hide()
            self.save_expander.hide()
        else:
            self.advanced_expander.show_all()
            self.save_expander.show_all()

        if self._ui is not None:
            self._ui.deactivate()

        new_ui.activate(options)

        self.update_size()

        self._ui = new_ui

    def update_size(self, widget=None):
        """Update the size of the dialog."""
        content_area = self.get_content_area()
        size = content_area.get_preferred_size()[0]
        self.resize(size.width, size.height)

    def run(self, options=None):
        """Popup new task dialog."""
        if options is None:
            self.set_ui(self.default_ui, {'uris': ''})
        elif 'torrent_filename' in options:
            self.set_ui(self.bt_ui, options)
        elif 'metalink_filename' in options:
            self.set_ui(self.ml_ui, options)
        else:
            self.set_ui(self.normal_ui, options)

        self.logger.info('Running new task dialog...')

        Gtk.Dialog.run(self)

