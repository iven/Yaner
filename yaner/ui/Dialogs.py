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
from gi.repository import Gio
from gi.repository.Gio import SettingsBindFlags as BindFlags

from yaner.Task import Task
from yaner.ui.Widgets import Box, Entry, SpinButton, Switch
from yaner.ui.Widgets import LeftAlignedLabel, AlignedExpander, URIsView
from yaner.ui.Widgets import MetafileChooserButton, FileChooserEntry
from yaner.ui.Widgets import HORIZONTAL, VERTICAL
from yaner.ui.PoolTree import PoolModel
from yaner.ui.CategoryComboBox import CategoryFilterModel, CategoryComboBox
from yaner.utils.Logging import LoggingMixin

_BT_FILTER_NAME = _('Torrent Files')
_ML_FILTER_NAME = _('Metalink Files')
_BT_MIME_TYPES = {'application/x-bittorrent'}
_ML_MIME_TYPES = {'application/metalink4+xml', 'application/metalink+xml'}

class _TaskNewUI(object):
    """Base class for the UIs of the new task dialog."""

    settings = Gio.Settings('com.kissuki.yaner.task')
    """GSettings instance for task configurations."""

    def __init__(self, setting_widgets, expander_label):
        self._setting_widgets = setting_widgets.copy()
        # Don't apply changes to dconf until apply() is called
        self.settings.delay()

        expander = AlignedExpander(expander_label)
        self._uris_expander = expander

        vbox = Box(VERTICAL)
        expander.add(vbox)
        self._content_box = vbox

    @property
    def uris_expander(self):
        return self._uris_expander

    def activate(self, options):
        """When the UI changed to this one, bind and update the setting widgets."""
        keys = self.settings.list_keys()
        for key, widget in self._setting_widgets.items():
            if key in keys:
                self.settings.bind(key, widget, 'value', BindFlags.DEFAULT)
            try:
                widget.value = options[key]
            except KeyError:
                pass
        self._uris_expander.show_all()

    def deactivate(self):
        """When the UI changed from this one, unbind the properties."""
        self.settings.revert()

class _TaskNewDefaultUI(_TaskNewUI):
    """Default UI of the new task dialog."""
    def __init__(self, setting_widgets, parent):
        _TaskNewUI.__init__(self, setting_widgets,
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
        entry.set_size_request(300, -1)
        box.pack_start(entry)
        self._setting_widgets['uris'] = entry

        self.uri_entry = entry

    def activate(self, options):
        _TaskNewUI.activate(self, options)
        self.uri_entry.grab_focus()

class _TaskNewNormalUI(_TaskNewUI):
    """Normal UI of the new task dialog."""
    def __init__(self, setting_widgets):
        _TaskNewUI.__init__(self, setting_widgets,
                            expander_label=_('<b>Mirrors</b> - one or more URI(s) for <b>one</b> task')
                           )

        box = self._content_box

        uris_view = URIsView()
        uris_view.set_size_request(300, 70)
        box.pack_start(uris_view)
        self._setting_widgets['uris'] = uris_view

        hbox = Box(HORIZONTAL)
        box.pack_start(hbox)

        # Rename
        label = LeftAlignedLabel(_('Rename:'))
        hbox.pack_start(label, expand=False)

        entry = Entry(activates_default=True)
        hbox.pack_start(entry)
        self._setting_widgets['out'] = entry

        # Connections
        label = LeftAlignedLabel(_('Connections:'))
        hbox.pack_start(label, expand=False)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        hbox.pack_start(spin_button)
        self._setting_widgets['split'] = spin_button

        self._uris_view = uris_view

    def activate(self, options):
        _TaskNewUI.activate(self, options)
        self._uris_view.grab_focus()

class _TaskNewBTUI(_TaskNewUI):
    """BT UI of the new task dialog."""
    def __init__(self, setting_widgets):
        _TaskNewUI.__init__(self, setting_widgets,
                            expander_label=_('<b>Torrent File</b>')
                           )

        box = self._content_box

        button = MetafileChooserButton(title=_('Select torrent file'),
                                       mime_types=_BT_MIME_TYPES,
                                      )
        button.set_size_request(300, -1)
        box.pack_start(button)
        self._setting_widgets['torrent_filename'] = button

class _TaskNewMLUI(_TaskNewUI):
    """Metalink UI of the new task dialog."""
    def __init__(self, setting_widgets):
        _TaskNewUI.__init__(self, setting_widgets,
                            expander_label=_('<b>Metalink File</b>')
                           )

        box = self._content_box

        button = MetafileChooserButton(title=_('Select metalink file'),
                                       mime_types=_ML_MIME_TYPES,
                                      )
        button.set_size_request(300, -1)
        box.pack_start(button)
        self._setting_widgets['metalink_filename'] = button

class TaskNewDialog(Gtk.Dialog, LoggingMixin):
    """Dialog for creating new tasks."""
    def __init__(self, parent, pool_model):
        """"""
        Gtk.Dialog.__init__(self, title=_('New Task'), parent=parent,
                            flags=(Gtk.DialogFlags.DESTROY_WITH_PARENT |
                                   Gtk.DialogFlags.MODAL),
                            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                     Gtk.STOCK_OK, Gtk.ResponseType.OK
                                    )
                           )
        LoggingMixin.__init__(self)

        self._ui = None
        self._default_ui = None
        self._normal_ui = None
        self._bt_ui = None
        self._ml_ui = None

        self._setting_widgets = {}

        ### Content Area
        content_area = self.get_content_area()

        vbox = Box(VERTICAL, border_width=5)
        content_area.add(vbox)
        self._main_vbox = vbox

        ## Save to
        expander = AlignedExpander(_('<b>Save to...</b>'))
        expander.connect_after('activate', self.update_size)
        vbox.pack_start(expander)

        hbox = Box(HORIZONTAL)
        expander.add(hbox)

        # Directory
        entry = FileChooserEntry(_('Select download directory'),
                                 self,
                                 Gtk.FileChooserAction.SELECT_FOLDER
                                )
        hbox.pack_end(entry)
        self._setting_widgets['dir'] = entry

        model = CategoryFilterModel(pool_model)
        combo_box = CategoryComboBox(model, self)
        combo_box.connect('changed', self._on_category_cb_changed, entry)
        combo_box.set_active(0)
        hbox.pack_start(combo_box)
        self._setting_widgets['category'] = combo_box

        ## Advanced
        expander = AlignedExpander(_('<b>Advanced</b>'), expanded=False)
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
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 0, 1)
        self._setting_widgets['max-upload-limit'] = spin_button

        label = LeftAlignedLabel(_('Download Limit(KiB/s):'))
        table.attach_defaults(label, 2, 3, 0, 1)

        adjustment = Gtk.Adjustment(lower=0, upper=4096, step_increment=10)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 0, 1)
        self._setting_widgets['max-download-limit'] = spin_button

        # Retry
        label = LeftAlignedLabel(_('Max Retries:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=60, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 1, 2)
        self._setting_widgets['max-tries'] = spin_button

        label = LeftAlignedLabel(_('Retry Interval(sec):'))
        table.attach_defaults(label, 2, 3, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=60, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 1, 2)
        self._setting_widgets['retry-wait'] = spin_button

        # Timeout
        label = LeftAlignedLabel(_('Timeout(sec):'))
        table.attach_defaults(label, 0, 1, 2, 3)

        adjustment = Gtk.Adjustment(lower=1, upper=300, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 2, 3)
        self._setting_widgets['timeout'] = spin_button

        label = LeftAlignedLabel(_('Connect Timeout(sec):'))
        table.attach_defaults(label, 2, 3, 2, 3)

        adjustment = Gtk.Adjustment(lower=1, upper=300, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 2, 3)
        self._setting_widgets['connect-timeout'] = spin_button

        # Split and Connections
        label = LeftAlignedLabel(_('Split Size(MiB):'))
        table.attach_defaults(label, 0, 1, 3, 4)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 3, 4)
        self._setting_widgets['min-split-size'] = spin_button

        label = LeftAlignedLabel(_('Per Server Connections:'))
        table.attach_defaults(label, 2, 3, 3, 4)

        adjustment = Gtk.Adjustment(lower=1, upper=10, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 3, 4)
        self._setting_widgets['max-connection-per-server'] = spin_button

        # Overwrite and Rename
        label = LeftAlignedLabel(_('Allow Overwrite:'))
        table.attach_defaults(label, 0, 1, 4, 5)

        switch = Switch()
        table.attach_defaults(switch, 1, 2, 4, 5)
        self._setting_widgets['allow-overwrite'] = switch

        label = LeftAlignedLabel(_('Auto Rename Files:'))
        table.attach_defaults(label, 2, 3, 4, 5)

        switch = Switch()
        table.attach_defaults(switch, 3, 4, 4, 5)
        self._setting_widgets['auto-file-renaming'] = switch

        # Referer
        hbox = Box(HORIZONTAL)
        vbox.pack_start(hbox, expand=False)

        label = LeftAlignedLabel(_('Referer:'))
        hbox.pack_start(label, expand=False)

        entry = Entry(activates_default=True)
        hbox.pack_start(entry)
        self._setting_widgets['referer'] = entry

        # Header
        hbox = Box(HORIZONTAL)
        vbox.pack_start(hbox, expand=False)

        label = LeftAlignedLabel(_('Header:'))
        hbox.pack_start(label, expand=False)

        entry = Entry(activates_default=True)
        hbox.pack_start(entry)
        self._setting_widgets['header'] = entry

        # Authorization
        expander = AlignedExpander(_('Authorization'), expanded=False)
        expander.connect_after('activate', self.update_size)
        vbox.pack_start(expander, expand=False)

        table = Gtk.Table(3, 3, False, row_spacing=5, column_spacing=5)
        expander.add(table)

        label = LeftAlignedLabel(_('HTTP:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        label = LeftAlignedLabel(_('FTP:'))
        table.attach_defaults(label, 0, 1, 2, 3)

        label = LeftAlignedLabel(_('User'))
        table.attach_defaults(label, 1, 2, 0, 1)

        label = LeftAlignedLabel(_('Password'))
        table.attach_defaults(label, 2, 3, 0, 1)

        entry = Entry(activates_default=True)
        table.attach_defaults(entry, 1, 2, 1, 2)
        self._setting_widgets['http-user'] = entry

        entry = Entry(activates_default=True)
        table.attach_defaults(entry, 2, 3, 1, 2)
        self._setting_widgets['http-passwd'] = entry

        entry = Entry(activates_default=True)
        table.attach_defaults(entry, 1, 2, 2, 3)
        self._setting_widgets['ftp-user'] = entry

        entry = Entry(activates_default=True)
        table.attach_defaults(entry, 2, 3, 2, 3)
        self._setting_widgets['ftp-passwd'] = entry

        ## BT Task Page
        label = Gtk.Label(_('BitTorrent'))
        vbox = Box(VERTICAL, border_width=5)
        notebook.append_page(vbox, label)

        table = Gtk.Table(2, 4, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(table, expand=False)

        # Limit
        label = LeftAlignedLabel(_('Max open files:'))
        table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 0, 1)
        self._setting_widgets['bt-max-open-files'] = spin_button

        label = LeftAlignedLabel(_('Max peers:'))
        table.attach_defaults(label, 2, 3, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 0, 1)
        self._setting_widgets['bt-max-peers'] = spin_button

        # Seed
        label = LeftAlignedLabel(_('Seed time(min):'))
        table.attach_defaults(label, 0, 1, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=7200, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 1, 2)
        self._setting_widgets['seed-time'] = spin_button

        label = LeftAlignedLabel(_('Seed ratio:'))
        table.attach_defaults(label, 2, 3, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=20, step_increment=.1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True, digits=1)
        table.attach_defaults(spin_button, 3, 4, 1, 2)
        self._setting_widgets['seed-ratio'] = spin_button

        # Timeout
        label = LeftAlignedLabel(_('Timeout(sec):'))
        table.attach_defaults(label, 0, 1, 2, 3)

        adjustment = Gtk.Adjustment(lower=1, upper=300, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 2, 3)
        self._setting_widgets['bt-tracker-timeout'] = spin_button

        label = LeftAlignedLabel(_('Connect Timeout(sec):'))
        table.attach_defaults(label, 2, 3, 2, 3)

        adjustment = Gtk.Adjustment(lower=1, upper=300, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 3, 4, 2, 3)
        self._setting_widgets['bt-tracker-connect-timeout'] = spin_button

        hbox = Box(HORIZONTAL)
        vbox.pack_start(hbox, expand=False)

        label = LeftAlignedLabel(_('Try to download first and last pieces first'))
        hbox.pack_start(label)
        switch = Switch()
        hbox.pack_start(switch, expand=False)
        self._setting_widgets['bt-prioritize'] = switch

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
        self._setting_widgets['uris'] = uris_view

        ## Metalink Page
        label = Gtk.Label(_('Metalink'))
        vbox = Box(VERTICAL, border_width=5)
        notebook.append_page(vbox, label)

        table = Gtk.Table(5, 2, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(table, expand=False)

        label = LeftAlignedLabel(_('Download Servers:'))
        table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=64, step_increment=1)
        spin_button = SpinButton(adjustment=adjustment, numeric=True)
        table.attach_defaults(spin_button, 1, 2, 0, 1)
        self._setting_widgets['metalink-servers'] = spin_button

        label = LeftAlignedLabel(_('Preferred locations:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        entry = Entry()
        table.attach_defaults(entry, 1, 2, 1, 2)
        self._setting_widgets['metalink-location'] = entry

        label = LeftAlignedLabel(_('Language:'))
        table.attach_defaults(label, 0, 1, 2, 3)

        entry = Entry()
        table.attach_defaults(entry, 1, 2, 2, 3)
        self._setting_widgets['metalink-language'] = entry

        label = LeftAlignedLabel(_('Version:'))
        table.attach_defaults(label, 0, 1, 3, 4)

        entry = Entry()
        table.attach_defaults(entry, 1, 2, 3, 4)
        self._setting_widgets['metalink-version'] = entry

        label = LeftAlignedLabel(_('OS:'))
        table.attach_defaults(label, 0, 1, 4, 5)

        entry = Entry()
        table.attach_defaults(entry, 1, 2, 4, 5)
        self._setting_widgets['metalink-os'] = entry

        self.show_all()

    @property
    def default_ui(self):
        """Get the default UI."""
        if self._default_ui is None:
            ui = _TaskNewDefaultUI(self._setting_widgets, self)
            ui.uri_entry.connect('response', self._on_metafile_selected)
            ui.uri_entry.connect('changed', self._on_default_entry_changed)
            self._default_ui = ui
        return self._default_ui

    @property
    def normal_ui(self):
        """Get the normal UI."""
        if self._normal_ui is None:
            self._normal_ui = _TaskNewNormalUI(self._setting_widgets)
        return self._normal_ui

    @property
    def bt_ui(self):
        """Get the BT UI."""
        if self._bt_ui is None:
            self._bt_ui = _TaskNewBTUI(self._setting_widgets)
        return self._bt_ui

    @property
    def ml_ui(self):
        """Get the ML UI."""
        if self._ml_ui is None:
            self._ml_ui = _TaskNewMLUI(self._setting_widgets)
        return self._ml_ui

    def _on_category_cb_changed(self, category_cb, entry):
        """When category combo box changed, update the directory entry."""
        iter_ = category_cb.get_active_iter()
        model = category_cb.get_model()
        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)
        entry.set_text(presentable.directory)
        self.logger.debug(_('Category is changed to {}.').format(presentable))

    def _on_metafile_selected(self, dialog, response_id):
        """When meta file chooser dialog responsed, switch to torrent or metalink
        mode."""
        if response_id == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            current_filter = dialog.get_filter().get_name()
            if current_filter == _BT_FILTER_NAME:
                self.set_ui(self.bt_ui, {'torrent_filename': filename})
            elif current_filter == _ML_FILTER_NAME:
                self.set_ui(self.ml_ui, {'metalink_filename': filename})
            else:
                raise RuntimeError('No such filter' + current_filter)

    def _on_default_entry_changed(self, entry):
        """When the entry in the default content box changed, switch to normal
        mode."""
        # When default UI activated, the entry text is cleared, we should
        # ignore this.
        if self._ui is not self.normal_ui:
            self.set_ui(self.normal_ui, {'uris': entry.get_text()})

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
            self.advanced_expander.hide()
        else:
            self.advanced_expander.show_all()

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
        #if 'header' in self._task_options:
        #    del self._task_options['header']

        if options is None:
            self.set_ui(self.default_ui, {'uris': ''})
        elif 'torrent_filename' in options:
            self.set_ui(self.bt_ui, options)
        elif 'metalink_filename' in options:
            self.set_ui(self.ml_ui, options)
        else:
            self.set_ui(self.normal_ui, options)

        self.logger.info(_('Running new task dialog...'))

        Gtk.Dialog.run(self)

class NormalTaskNewDialog(TaskNewDialog):
    """New task dialog for normal tasks."""
    def __init__(self, parent, pool_model):
        TaskNewDialog.__init__(self, parent, pool_model)

        ## Main Box
        expander = AlignedExpander(
            _('<b>Mirrors</b> - one or more URI(s) for <b>one</b> task'))
        self.main_vbox.pack_start(expander)

        vbox = Box(VERTICAL)
        expander.add(vbox)

        uris_view = URIsView()
        vbox.pack_start(uris_view)
        self.bind('uris', uris_view, 'uris', bind_settings=False)
        self.uris_view = uris_view

        hbox = Box(HORIZONTAL)
        vbox.pack_start(hbox)

        # Rename
        rename_label = LeftAlignedLabel(_('Rename:'))
        hbox.pack_start(rename_label, expand=False)

        rename_entry = Gtk.Entry(activates_default=True)
        hbox.pack_start(rename_entry)
        self.bind('out', rename_entry, 'text', bind_settings=False)
        self.rename_entry = rename_entry

        # Connections
        split_label = LeftAlignedLabel(_('Connections:'))
        hbox.pack_start(split_label, expand=False)

        split_adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        split_button = Gtk.SpinButton(adjustment=split_adjustment, numeric=True)
        hbox.pack_start(split_button)
        self.bind('split', split_button, 'value')

        self.main_vbox.show_all()

        ## Advanced
        hbox = Box(HORIZONTAL)
        self.advanced_box.pack_start(hbox)

        # Referer
        referer_label = LeftAlignedLabel(_('Referer:'))
        hbox.pack_start(referer_label, expand=False)

        referer_entry = Gtk.Entry(activates_default=True)
        hbox.pack_start(referer_entry)
        self.bind('referer', referer_entry, 'text')
        self.referer_entry = referer_entry

        # Authorization
        auth_expander = AlignedExpander(_('Authorization'), expanded=False)
        self.advanced_box.pack_start(auth_expander)

        auth_table = Gtk.Table(3, 3, False, row_spacing=5, column_spacing=5)
        auth_expander.add(auth_table)

        http_label = LeftAlignedLabel(_('HTTP:'))
        auth_table.attach_defaults(http_label, 0, 1, 1, 2)

        ftp_label = LeftAlignedLabel(_('FTP:'))
        auth_table.attach_defaults(ftp_label, 0, 1, 2, 3)

        user_label = LeftAlignedLabel(_('User'))
        auth_table.attach_defaults(user_label, 1, 2, 0, 1)

        passwd_label = LeftAlignedLabel(_('Password'))
        auth_table.attach_defaults(passwd_label, 2, 3, 0, 1)

        http_user_entry = Gtk.Entry(activates_default=True)
        auth_table.attach_defaults(http_user_entry, 1, 2, 1, 2)
        self.bind('http-user', http_user_entry, 'text')

        http_passwd_entry = Gtk.Entry(activates_default=True)
        auth_table.attach_defaults(http_passwd_entry, 2, 3, 1, 2)
        self.bind('http-passwd', http_passwd_entry, 'text')

        ftp_user_entry = Gtk.Entry(activates_default=True)
        auth_table.attach_defaults(ftp_user_entry, 1, 2, 2, 3)
        self.bind('ftp-user', ftp_user_entry, 'text')

        ftp_passwd_entry = Gtk.Entry(activates_default=True)
        auth_table.attach_defaults(ftp_passwd_entry, 2, 3, 2, 3)
        self.bind('ftp-passwd', ftp_passwd_entry, 'text')

        self.advanced_box.show_all()

    def do_response(self, response):
        """Create a new download task if uris are provided."""
        if response != Gtk.ResponseType.OK:
            self.hide()
            return

        options = self.task_options.copy()
        uris = options.pop('uris')
        if not uris:
            return

        name = options['out'] if options['out'] else os.path.basename(uris[0])
        category = options.pop('category')

        # SpinButton returns double, but aria2 expects integer
        options['split'] = int(options['split'])

        Task(name=name, uris=uris, options=options, category=category).start()

        self.hide()

    def run(self, options=None):
        """Run the dialog."""
        self.uris_view.set_uris('')
        self.referer_entry.set_text('')
        self.rename_entry.set_text('')
        if options is not None:
            if 'uris' in options:
                self.uris_view.set_uris(options.pop('uris'))
            if 'referer' in options:
                self.referer_entry.set_text(options.pop('referer'))
            if 'out' in options:
                self.rename_entry.set_text(options.pop('out'))

        TaskNewDialog.run(self, options)

class BTTaskNewDialog(TaskNewDialog):
    """New task dialog for BT tasks."""
    def __init__(self, parent, pool_model):
        TaskNewDialog.__init__(self, parent, pool_model)

        ## Main Box
        expander = AlignedExpander(_('<b>Torrent file</b>'))
        self.main_vbox.pack_start(expander)

        button = MetafileChooserButton(title=_('Select torrent file'),
                                       mime_types=_BT_MIME_TYPES,
                                      )
        expander.add(button)
        self.bind('torrent_filename', button, 'filename', bind_settings=False)

        self.main_vbox.show_all()

        ## Advanced
        # Settings
        expander = AlignedExpander(_('Settings'))
        self.advanced_box.pack_start(expander)

        vbox = Box(VERTICAL)
        expander.add(vbox)

        settings_table = Gtk.Table(2, 4, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(settings_table)

        label = LeftAlignedLabel(_('Max open files:'))
        settings_table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        settings_table.attach_defaults(spin_button, 1, 2, 0, 1)
        self.bind('bt-max-open-files', spin_button, 'value')

        label = LeftAlignedLabel(_('Max peers:'))
        settings_table.attach_defaults(label, 2, 3, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        settings_table.attach_defaults(spin_button, 3, 4, 0, 1)
        self.bind('bt-max-peers', spin_button, 'value')

        label = LeftAlignedLabel(_('Seed time(min):'))
        settings_table.attach_defaults(label, 0, 1, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=7200, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        settings_table.attach_defaults(spin_button, 1, 2, 1, 2)
        self.bind('seed-time', spin_button, 'value')

        label = LeftAlignedLabel(_('Seed ratio:'))
        settings_table.attach_defaults(label, 2, 3, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=20, step_increment=.1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True, digits=1)
        settings_table.attach_defaults(spin_button, 3, 4, 1, 2)
        self.bind('seed-ratio', spin_button, 'value')

        check_button = Gtk.CheckButton(
            label=_('Preview mode'),
            tooltip_text=_('Try to download first and last pieces first'))
        vbox.pack_start(check_button)
        self.bind('bt-prioritize', check_button, 'active')

        # Mirrors
        expander = AlignedExpander(_('Mirrors'), expanded=False)
        expander.set_tooltip_text(
            _('For single file torrents, a mirror can be a ' \
              'complete URI pointing to the resource or if the mirror ' \
              'ends with /, name in torrent file is added. For ' \
              'multi-file torrents, name and path in torrent are ' \
              'added to form a URI for each file.'))
        self.advanced_box.pack_start(expander)

        vbox = Box(VERTICAL)
        expander.add(vbox)

        uris_view = URIsView()
        vbox.pack_start(uris_view)
        self.bind('uris', uris_view, 'uris', bind_settings=False)
        self.uris_view = uris_view

        self.advanced_box.show_all()

    def do_response(self, response):
        """Create a new download task if uris are provided."""
        if response != Gtk.ResponseType.OK:
            self.hide()
            return

        options = self.task_options.copy()

        torrent_filename = options.pop('torrent_filename')
        if torrent_filename is None:
            return
        else:
            name = os.path.basename(torrent_filename)
            with open(torrent_filename, 'br') as torrent_file:
                torrent = xmlrpc.client.Binary(torrent_file.read())

        uris = options.pop('uris')
        category = options.pop('category')
        if options.pop('bt-prioritize'):
            options['bt-prioritize-size'] = 'head,tail'
        for key in ('seed-time', 'bt-max-open-files', 'bt-max-peers'):
            options[key] = int(options[key])

        Task(name=name, torrent=torrent, uris=uris,
             options=options, category=category).start()

        self.hide()

    def run(self, options=None):
        """Run the dialog."""
        self.uris_view.set_uris('')

        TaskNewDialog.run(self, options)

class MLTaskNewDialog(TaskNewDialog):
    """New task dialog for Metalink tasks."""
    def __init__(self, parent, pool_model):
        TaskNewDialog.__init__(self, parent, pool_model)

        ## Main Box
        expander = AlignedExpander(_('<b>Metalink file</b>'))
        self.main_vbox.pack_start(expander)

        button = MetafileChooserButton(title=_('Select metalink file'),
                                       mime_types=_ML_MIME_TYPES,
                                      )
        expander.add(button)
        self.bind('metalink_filename', button, 'filename', bind_settings=False)

        self.main_vbox.show_all()

        ## Advanced
        # Settings
        expander = AlignedExpander(_('Settings'))
        self.advanced_box.pack_start(expander)

        vbox = Box(VERTICAL)
        expander.add(vbox)

        settings_table = Gtk.Table(5, 2, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(settings_table)

        label = LeftAlignedLabel(_('Download Servers:'))
        settings_table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=64, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        settings_table.attach_defaults(spin_button, 1, 2, 0, 1)
        self.bind('metalink-servers', spin_button, 'value')

        label = LeftAlignedLabel(_('Preferred locations:'))
        settings_table.attach_defaults(label, 0, 1, 1, 2)

        entry = Gtk.Entry()
        settings_table.attach_defaults(entry, 1, 2, 1, 2)
        self.bind('metalink-location', entry, 'text')

        label = LeftAlignedLabel(_('Language:'))
        settings_table.attach_defaults(label, 0, 1, 2, 3)

        entry = Gtk.Entry()
        settings_table.attach_defaults(entry, 1, 2, 2, 3)
        self.bind('metalink-language', entry, 'text')

        label = LeftAlignedLabel(_('Version:'))
        settings_table.attach_defaults(label, 0, 1, 3, 4)

        entry = Gtk.Entry()
        settings_table.attach_defaults(entry, 1, 2, 3, 4)
        self.bind('metalink-version', entry, 'text')

        label = LeftAlignedLabel(_('OS:'))
        settings_table.attach_defaults(label, 0, 1, 4, 5)

        entry = Gtk.Entry()
        settings_table.attach_defaults(entry, 1, 2, 4, 5)
        self.bind('metalink-os', entry, 'text')

        self.advanced_box.show_all()

    def do_response(self, response):
        """Create a new download task if uris are provided."""
        if response != Gtk.ResponseType.OK:
            self.hide()
            return

        options = self.task_options.copy()

        metalink_filename = options.pop('metalink_filename')
        if metalink_filename is None:
            return
        else:
            name = os.path.basename(metalink_filename)
            with open(metalink_filename, 'br') as metalink_file:
                metafile = xmlrpc.client.Binary(metalink_file.read())

        category = options.pop('category')
        options['metalink-servers'] = int(options['metalink-servers'])

        Task(name=name, metafile=metafile, options=options,
             category=category).start()

        self.hide()

class CategoryBar(Gtk.InfoBar):
    """A InfoBar used to adding or editing categories."""
    def __init__(self, pool, parent):
        Gtk.InfoBar.__init__(self, message_type=Gtk.MessageType.OTHER)

        widgets = {}
        content_area = self.get_content_area()

        table = Gtk.Table(2, 2, False, row_spacing=5, column_spacing=5)
        content_area.pack_start(table, True, True, 0)

        label = LeftAlignedLabel(_('Category Name:'))
        table.attach_defaults(label, 0, 1, 0, 1)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 0, 1)
        widgets['name'] = entry

        label = LeftAlignedLabel(_('Default directory:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        entry = FileChooserEntry(_('Select default directory'), parent,
                                 Gtk.FileChooserAction.SELECT_FOLDER)
        table.attach_defaults(entry, 1, 2, 1, 2)
        widgets['directory'] = entry

        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self.pool = pool
        self.category = None
        self.widgets = widgets

    def update(self, pool, category=None):
        """Update the category bar using the given pool and category. If category
        is None, this will set all widgets to empty, and switch to category
        adding mode."""
        self.category = category
        self.pool = pool

        for prop in ('name', 'directory'):
            text = getattr(category, prop, '')
            self.widgets[prop].set_text(text)

class PoolBar(Gtk.InfoBar):
    """A InfoBar used to adding or editing pool."""
    def __init__(self):
        Gtk.InfoBar.__init__(self, message_type=Gtk.MessageType.OTHER)

        widgets = {}
        content_area = self.get_content_area()

        table = Gtk.Table(5, 2, False, row_spacing=5, column_spacing=5)
        content_area.pack_start(table, True, True, 0)

        label = LeftAlignedLabel(_('Server Name:'))
        table.attach_defaults(label, 0, 1, 0, 1)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 0, 1)
        widgets['name'] = entry

        label = LeftAlignedLabel(_('IP Address:'))
        table.attach_defaults(label, 0, 1, 1, 2)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 1, 2)
        widgets['host'] = entry

        label = LeftAlignedLabel(_('Port:'))
        table.attach_defaults(label, 0, 1, 2, 3)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 2, 3)
        widgets['port'] = entry

        label = LeftAlignedLabel(_('User:'))
        table.attach_defaults(label, 0, 1, 3, 4)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 3, 4)
        widgets['user'] = entry

        label = LeftAlignedLabel(_('Password:'))
        table.attach_defaults(label, 0, 1, 4, 5)

        entry = Gtk.Entry()
        table.attach_defaults(entry, 1, 2, 4, 5)
        widgets['passwd'] = entry

        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self.pool = None
        self.widgets = widgets

    def update(self, pool=None):
        """Update the pool bar using the given pool. If pool is None, this
        will set all widgets to empty, and switch to pool adding mode."""
        self.pool = pool

        for prop in ('name', 'host', 'port', 'user', 'passwd'):
            text = getattr(pool, prop, '')
            self.widgets[prop].set_text(text)

