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
from gi.repository import GObject
from gi.repository import Pango
from gi.repository.Gio import SettingsBindFlags as BindFlags

from yaner import SQLSession
from yaner.Pool import Pool
from yaner.Task import Task, NormalTask, BTTask, MLTask
from yaner.Presentable import Presentable, Category
from yaner.ui.Misc import load_ui_file
from yaner.ui.Widgets import AlignedExpander, URIsView
from yaner.ui.PoolTree import PoolModel
from yaner.utils.Logging import LoggingMixin
from yaner.utils.Configuration import ConfigParser

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

        torrent_button = Gtk.FileChooserButton(title=_('Select torrent file'))
        expander.add(torrent_button)

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

        self.hide()

    def run(self, options=None):
        """Run the dialog."""
        self.uris_view.set_uris('')

        TaskNewDialog.run(self, options)




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

class TaskNewDialogOld(TaskDialogMixin):
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

