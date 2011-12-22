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
from gi.repository.Gio import SettingsBindFlags as BindFlags

from yaner.Task import Task, NormalTask, BTTask, MLTask
from yaner.Presentable import Presentable
from yaner.ui.Widgets import AlignedExpander, URIsView
from yaner.ui.PoolTree import PoolModel

class TaskNewDialog(Gtk.Dialog):
    """Base class for all new task dialogs."""

    settings = Gio.Settings('com.kissuki.yaner.task')
    """GSettings instance for task configurations."""

    def __init__(self, parent, pool_model):
        Gtk.Dialog.__init__(self, title=_('New Task'), parent=parent,
                            flags=(Gtk.DialogFlags.DESTROY_WITH_PARENT |
                                   Gtk.DialogFlags.MODAL),
                            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                     Gtk.STOCK_OK, Gtk.ResponseType.OK
                                    )
                           )

        self.task_options = {}
        self.active_category = None

        ### Content Area
        content_area = self.get_content_area()

        vbox = Gtk.VBox(spacing=5)
        vbox.set_border_width(5)
        content_area.add(vbox)
        self.main_vbox = vbox

        ## Advanced
        expander = AlignedExpander(_('<b>Advanced</b>'), expanded=False)
        vbox.pack_end(expander, expand=True, fill=True, padding=0)

        advanced_box = Gtk.VBox(spacing=5)
        expander.add(advanced_box)
        self.advanced_box = advanced_box

        ## Save to
        expander = AlignedExpander(_('<b>Save to...</b>'))
        vbox.pack_end(expander, expand=True, fill=True, padding=0)

        # Category
        hbox = Gtk.HBox(spacing=5)
        expander.add(hbox)

        category_model = Gtk.TreeModelFilter(child_model=pool_model)
        category_model.set_visible_func(self._category_visible_func, None)

        category_cb = Gtk.ComboBox(model=category_model)
        hbox.pack_start(category_cb, expand=False, fill=True, padding=0)

        renderer = Gtk.CellRendererPixbuf()
        category_cb.pack_start(renderer, False)
        category_cb.set_cell_data_func(renderer, self._pixbuf_data_func, None)

        renderer = Gtk.CellRendererText()
        category_cb.pack_start(renderer, True)
        category_cb.set_cell_data_func(renderer, self._markup_data_func, None)

        # Directory
        dir_entry = Gtk.Entry()
        hbox.pack_start(dir_entry, expand=True, fill=True, padding=0)
        self.bind('dir', dir_entry, 'text')

        dir_chooser_button = Gtk.Button(label=_('_Browse...'), use_underline=True)
        dir_chooser_button.connect('clicked', self._on_dir_choosing, dir_entry)
        hbox.pack_start(dir_chooser_button, expand=False, fill=True, padding=0)

        # Connect signal and select the first pool
        category_cb.connect('changed', self._on_category_cb_changed, dir_entry)
        category_cb.set_active(0)

        content_area.show_all()

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
        return presentable.TYPE in (Presentable.TYPES.CATEGORY,
                                    Presentable.TYPES.QUEUING)

    def _on_category_cb_changed(self, category_cb, dir_entry):
        """When category combobox changed, update the directory entry."""
        iter_ = category_cb.get_active_iter()
        model = category_cb.get_model()
        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)
        if presentable.TYPE == Presentable.TYPES.QUEUING:
            category_cb.set_active_iter(model.iter_children(iter_))
        else:
            self.active_category = presentable
            dir_entry.set_text(presentable.directory)

    def _on_dir_choosing(self, button, entry):
        """When directory chooser button clicked, popup the dialog, and update
        the directory entry.
        """
        dialog = Gtk.FileChooserDialog(_('Select download directory'),
                                       self,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT
                                       )
                                      )
        dialog.set_transient_for(self.get_parent())
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            entry.set_text(dialog.get_filename())
        dialog.destroy()

    def bind(self, name, widget, property,
             bind_settings=True, bind_flags=BindFlags.GET,
             bind_signal=True, signal_name='changed'):
        """Bind property to settings and task options."""

        def signal_callback(widget):
            """When widget changed, add new value to the task opti)ns."""
            self.task_options[name] = widget.get_property(property)

        if bind_settings:
            self.settings.bind(name, widget, property, bind_flags)
        if bind_signal:
            widget.connect(signal_name, signal_callback)
            widget.emit(signal_name)

    def run(self, options=None):
        """Popup new task dialog."""
        if 'header' in self.task_options:
            del self.task_options['header']
        if options is not None:
            self.task_options.update(options)
        Gtk.Dialog.run(self)

class NormalTaskNewDialog(TaskNewDialog):
    """New task dialog for normal tasks."""
    def __init__(self, parent, pool_model):
        TaskNewDialog.__init__(self, parent, pool_model)

        ## Main Box
        expander = AlignedExpander(
            _('<b>Mirrors</b> - one or more URI(s) for <b>one</b> task'))
        self.main_vbox.pack_start(expander, expand=True, fill=True, padding=0)

        vbox = Gtk.VBox(spacing=5)
        expander.add(vbox)

        uris_view = URIsView()
        vbox.pack_start(uris_view, expand=True, fill=True, padding=0)
        self.uris_view = uris_view

        hbox = Gtk.HBox(spacing=5)
        vbox.pack_start(hbox, expand=True, fill=True, padding=0)

        # Rename
        rename_label = Gtk.Label(_('Rename'))
        hbox.pack_start(rename_label, expand=False, fill=True, padding=0)

        rename_entry = Gtk.Entry(activates_default=True)
        hbox.pack_start(rename_entry, expand=True, fill=True, padding=0)
        self.bind('out', rename_entry, 'text', bind_settings=False)
        self.rename_entry = rename_entry

        # Connections
        split_label = Gtk.Label(_('Connections'))
        hbox.pack_start(split_label, expand=False, fill=True, padding=0)

        split_adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        split_button = Gtk.SpinButton(adjustment=split_adjustment, numeric=True)
        hbox.pack_start(split_button, expand=True, fill=True, padding=0)
        self.bind('split', split_button, 'value')

        self.main_vbox.show_all()

        ## Advanced
        hbox = Gtk.HBox(spacing=5)
        self.advanced_box.pack_start(hbox, expand=True, fill=True, padding=0)

        # Referer
        referer_label = Gtk.Label(_('Referer'))
        hbox.pack_start(referer_label, expand=False, fill=True, padding=0)

        referer_entry = Gtk.Entry(activates_default=True)
        hbox.pack_start(referer_entry, expand=True, fill=True, padding=0)
        self.bind('referer', referer_entry, 'text')
        self.referer_entry = referer_entry

        # Authorization
        auth_expander = AlignedExpander(_('Authorization'), expanded=False)
        self.advanced_box.pack_start(auth_expander, expand=True,
                                     fill=True, padding=0)

        auth_table = Gtk.Table(3, 3, False, row_spacing=5, column_spacing=5)
        auth_expander.add(auth_table)

        http_label = Gtk.Label(_('HTTP'))
        auth_table.attach_defaults(http_label, 0, 1, 1, 2)

        ftp_label = Gtk.Label(_('FTP'))
        auth_table.attach_defaults(ftp_label, 0, 1, 2, 3)

        user_label = Gtk.Label(_('User'))
        auth_table.attach_defaults(user_label, 1, 2, 0, 1)

        passwd_label = Gtk.Label(_('Password'))
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

        uris = self.uris_view.get_uris()
        if not uris:
            return

        options = self.task_options
        name = options['out'] if options['out'] else os.path.basename(uris[0])
        # SpinButton returns double, but aria2 expects integer
        options['split'] = int(options['split'])

        NormalTask(name=name, type=Task.TYPES.NORMAL, uris=uris,
                   options=options, category=self.active_category,
                   pool=self.active_category.pool).start()

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
        self.main_vbox.pack_start(expander, expand=True, fill=True, padding=0)

        file_filter = Gtk.FileFilter()
        file_filter.add_mime_type('application/x-bittorrent')
        torrent_button = Gtk.FileChooserButton(title=_('Select torrent file'),
                                               filter=file_filter)
        expander.add(torrent_button)
        self.torrent_button = torrent_button

        self.main_vbox.show_all()

        ## Advanced
        # Settings
        expander = AlignedExpander(_('Settings'))
        self.advanced_box.pack_start(expander, expand=True, fill=True, padding=0)

        vbox = Gtk.VBox(spacing=5)
        expander.add(vbox)

        settings_table = Gtk.Table(2, 4, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(settings_table, expand=True, fill=True, padding=0)

        label = Gtk.Label(_('Max open files:'))
        settings_table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        settings_table.attach_defaults(spin_button, 1, 2, 0, 1)
        self.bind('bt-max-open-files', spin_button, 'value')

        label = Gtk.Label(_('Max peers:'))
        settings_table.attach_defaults(label, 2, 3, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=1024, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        settings_table.attach_defaults(spin_button, 3, 4, 0, 1)
        self.bind('bt-max-peers', spin_button, 'value')

        label = Gtk.Label(_('Seed time(min):'))
        settings_table.attach_defaults(label, 0, 1, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=7200, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        settings_table.attach_defaults(spin_button, 1, 2, 1, 2)
        self.bind('seed-time', spin_button, 'value')

        label = Gtk.Label(_('Seed ratio:'))
        settings_table.attach_defaults(label, 2, 3, 1, 2)

        adjustment = Gtk.Adjustment(lower=0, upper=20, step_increment=.1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True, digits=1)
        settings_table.attach_defaults(spin_button, 3, 4, 1, 2)
        self.bind('seed-ratio', spin_button, 'value')

        check_button = Gtk.CheckButton(
            label=_('Preview mode'),
            tooltip_text=_('Try to download first and last pieces first'))
        vbox.pack_start(check_button, expand=True, fill=True, padding=0)
        self.bind('bt-prioritize', check_button, 'active', signal_name='toggled')

        # Mirrors
        expander = AlignedExpander(_('Mirrors'), expanded=False)
        expander.set_tooltip_text(
            _('For single file torrents, a mirror can be a ' \
              'complete URI pointing to the resource or if the mirror ' \
              'ends with /, name in torrent file is added. For ' \
              'multi-file torrents, name and path in torrent are ' \
              'added to form a URI for each file.'))
        self.advanced_box.pack_start(expander, expand=True, fill=True, padding=0)

        vbox = Gtk.VBox(spacing=5)
        expander.add(vbox)

        uris_view = URIsView()
        vbox.pack_start(uris_view, expand=True, fill=True, padding=0)
        self.uris_view = uris_view

        self.advanced_box.show_all()

    def do_response(self, response):
        """Create a new download task if uris are provided."""
        if response != Gtk.ResponseType.OK:
            self.hide()
            return

        uris = self.uris_view.get_uris()
        torrent_filename = self.torrent_button.get_filename()
        if torrent_filename is None:
            return
        else:
            name = os.path.basename(torrent_filename)
            with open(torrent_filename, 'br') as torrent_file:
                metafile = xmlrpc.client.Binary(torrent_file.read())

        options = self.task_options
        if options.pop('bt-prioritize'):
            options['bt-prioritize-size'] = 'head,tail'
        for key in ('seed-time', 'bt-max-open-files', 'bt-max-peers'):
            options[key] = int(options[key])

        BTTask(name=name, type=Task.TYPES.BT, metafile=metafile, uris=uris,
               options=options, category=self.active_category,
               pool=self.active_category.pool).start()

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
        self.main_vbox.pack_start(expander, expand=True, fill=True, padding=0)

        file_filter = Gtk.FileFilter()
        file_filter.add_mime_type('application/metalink4+xml')
        file_filter.add_mime_type('application/metalink+xml')
        button = Gtk.FileChooserButton(title=_('Select metalink file'),
                                               filter=file_filter)
        expander.add(button)
        self.metalink_button = button

        self.main_vbox.show_all()

        ## Advanced
        # Settings
        expander = AlignedExpander(_('Settings'))
        self.advanced_box.pack_start(expander, expand=True, fill=True, padding=0)

        vbox = Gtk.VBox(spacing=5)
        expander.add(vbox)

        settings_table = Gtk.Table(5, 2, False, row_spacing=5, column_spacing=5)
        vbox.pack_start(settings_table, expand=True, fill=True, padding=0)

        label = Gtk.Label(_('Download Servers:'))
        settings_table.attach_defaults(label, 0, 1, 0, 1)

        adjustment = Gtk.Adjustment(lower=1, upper=64, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment, numeric=True)
        settings_table.attach_defaults(spin_button, 1, 2, 0, 1)
        self.bind('metalink-servers', spin_button, 'value')

        label = Gtk.Label(_('Preferred locations'))
        settings_table.attach_defaults(label, 0, 1, 1, 2)

        entry = Gtk.Entry()
        settings_table.attach_defaults(entry, 1, 2, 1, 2)
        self.bind('metalink-location', entry, 'text')

        label = Gtk.Label(_('Language'))
        settings_table.attach_defaults(label, 0, 1, 2, 3)

        entry = Gtk.Entry()
        settings_table.attach_defaults(entry, 1, 2, 2, 3)
        self.bind('metalink-language', entry, 'text')

        label = Gtk.Label(_('Version'))
        settings_table.attach_defaults(label, 0, 1, 3, 4)

        entry = Gtk.Entry()
        settings_table.attach_defaults(entry, 1, 2, 3, 4)
        self.bind('metalink-version', entry, 'text')

        label = Gtk.Label(_('OS'))
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

        metalink_filename = self.metalink_button.get_filename()
        if metalink_filename is None:
            return
        else:
            name = os.path.basename(metalink_filename)
            with open(metalink_filename, 'br') as metalink_file:
                metafile = xmlrpc.client.Binary(metalink_file.read())

        options = self.task_options
        options['metalink-servers'] = int(options['metalink-servers'])

        MLTask(name=name, type=Task.TYPES.ML, metafile=metafile,
               options=options, category=self.active_category,
               pool=self.active_category.pool).start()

        self.hide()

