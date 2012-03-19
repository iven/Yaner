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
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import Pango

from yaner.Task import Task
from yaner.Presentable import Presentable
from yaner.ui.Widgets import LeftAlignedLabel, AlignedExpander, URIsView, Box
from yaner.ui.Widgets import MetafileChooserButton, FileChooserEntry
from yaner.ui.Widgets import HORIZONTAL, VERTICAL
from yaner.ui.PoolTree import PoolModel
from yaner.utils.Logging import LoggingMixin

class _SettingWidget(LoggingMixin):
    """A widget for communicate with GSettings."""
    def __init__(self, settings):
        LoggingMixin.__init__(self)

        self.settings = settings

    def get(self):
        """Get the task options to be used for aria2 from the widget status."""
        return {}

    def set(self, options):
        """Set the widget status according to the options provided."""
        pass

    def load(self):
        """Load settings from GSettings and set the value of the widget."""
        pass

    def save(self):
        """Save the value of the widget to GSettings."""
        pass

class _SettingEntry(Gtk.Entry, _SettingWidget):
    """An entry for communicate with GSettings."""
    def __init__(self, settings, key):
        Gtk.Entry.__init__(self)
        _SettingWidget.__init__(self, settings)

        self._key = key

    def get(self):
        return {self._key: self.get_text()}

    def set(self, options):
        try:
            self.set_text(options[self._key])
        except KeyError:
            pass

    def load(self):
        self.set_text(self.settings.get(self.key))

    def save(self):
        self.settings.set(self.key, self.get_text())

class _SettingDirBox(Box, _SettingWidget):
    """ComboBox and Entry for the directory option."""
    def __init__(self, settings, pool_model, parent):
        Box.__init__(self, HORIZONTAL)
        _SettingWidget.__init__(self, settings)

        self._active_category = None

        category_model = Gtk.TreeModelFilter(child_model=pool_model)
        category_model.set_visible_func(self._category_visible_func, None)

        category_cb = Gtk.ComboBox(model=category_model)
        self.pack_start(category_cb)

        renderer = Gtk.CellRendererPixbuf()
        category_cb.pack_start(renderer, False)
        category_cb.set_cell_data_func(renderer, self._pixbuf_data_func, None)

        renderer = Gtk.CellRendererText()
        category_cb.pack_start(renderer, True)
        category_cb.set_cell_data_func(renderer, self._markup_data_func, None)

        # Directory
        dir_entry = FileChooserEntry(_('Select download directory'), parent,
                                     Gtk.FileChooserAction.SELECT_FOLDER)
        self.pack_start(dir_entry)
        self._dir_entry = dir_entry

        # Connect signal and select the first pool
        category_cb.connect('changed', self._on_category_cb_changed, dir_entry)
        category_cb.set_active(0)

    def _pixbuf_data_func(self, cell_layout, renderer, model, iter_, data=None):
        """Method for set the icon and its size in the column."""
        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)

        if presentable.TYPE == Presentable.TYPES.QUEUING:
            if presentable.pool.connected:
                icon = 'gtk-connect'
            else:
                icon = 'gtk-disconnect'
        elif presentable.TYPE == Presentable.TYPES.CATEGORY:
            icon = 'gtk-directory'

        renderer.set_properties(
                stock_id = icon,
                stock_size = Gtk.IconSize.LARGE_TOOLBAR,
                )

    def _markup_data_func(self, cell_layout, renderer, model, iter_, data=None):
        """
        Method for format the text in the column.
        """
        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)

        renderer.set_properties(
                markup = GLib.markup_escape_text(presentable.name),
                ellipsize_set = True,
                ellipsize = Pango.EllipsizeMode.MIDDLE,
                )

    def _category_visible_func(self, model, iter_, data):
        """Show categorys of the selected pool in the combobox."""
        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)
        return (presentable is not None and 
                presentable.TYPE in (Presentable.TYPES.CATEGORY,
                                     Presentable.TYPES.QUEUING)
               )

    def _on_category_cb_changed(self, category_cb, dir_entry):
        """When category combobox changed, update the directory entry."""
        iter_ = category_cb.get_active_iter()
        model = category_cb.get_model()

        if iter_ is None:
            category_cb.set_active_iter(model.iter_children(iter_))
            return

        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)
        if presentable.TYPE == Presentable.TYPES.QUEUING:
            category_cb.set_active_iter(model.iter_children(iter_))
        else:
            self._active_category = presentable
            dir_entry.set_text(presentable.directory)
            self.logger.debug(_('Category is changed to {}.').format(presentable))

    def get(self):
        return {
            'dir': self._dir_entry.get_text(),
            'category': self._active_category,
        }

    def set(self, options):
        try:
            self._dir_entry.set_text(options[self._key])
        except KeyError:
            pass

class TaskNewDialog(Gtk.Dialog, LoggingMixin):
    """Dialog for creating new tasks."""

    settings = Gio.Settings('com.kissuki.yaner.task')
    """GSettings instance for task configurations."""

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

        self.task_options = {}
        self._default_content_box = None

        ### Content Area
        content_area = self.get_content_area()

        vbox = Box(VERTICAL)
        vbox.set_border_width(5)
        content_area.add(vbox)
        self.main_vbox = vbox

        ## Advanced
        expander = AlignedExpander(_('<b>Advanced</b>'), expanded=False)
        vbox.pack_end(expander)

        advanced_box = Box(VERTICAL)
        expander.add(advanced_box)
        self.advanced_box = advanced_box

        ## Save to
        expander = AlignedExpander(_('<b>Save to...</b>'))
        vbox.pack_end(expander)

        dir_box = _SettingDirBox(self.settings, pool_model, self)
        expander.add(dir_box)
        
        vbox.pack_end(self.default_content_box)

        self.default_content_box.show_all()
        vbox.show()
        self.show()

    @property
    def default_content_box(self):
        """Get the default content box."""
        if self._default_content_box is None:
            content_box = Box(HORIZONTAL)

            label = LeftAlignedLabel(_('URI(s):'))
            content_box.pack_start(label)

            entry = FileChooserEntry(_('Select Torrent/Metalink Files'),
                                     self,
                                     Gtk.FileChooserAction.OPEN,
                                     {
                                         'name': _('Torrent/Metalink Files'),
                                         'types':(
                                             'application/x-bittorrent',
                                             'application/metalink4+xml',
                                             'application/metalink+xml',
                                         ),
                                     },
                                     truncate_multiline=True,
                                     width_chars=50,
                                    )

            content_box.pack_start(entry)

            self._default_content_box = content_box
        return self._default_content_box

    def run(self, options=None):
        """Popup new task dialog."""
        if 'header' in self.task_options:
            del self.task_options['header']
        if options is not None:
            self.task_options.update(options)

        self.logger.info(_('Running new task dialog...'))
        self.logger.debug(_('Task options: {}').format(self.task_options))

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
                                       mime_types=['application/x-bittorrent']
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
                                       mime_types=['application/metalink4+xml',
                                                   'application/metalink+xml']
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

