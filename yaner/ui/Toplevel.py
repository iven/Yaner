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
This module contains the toplevel window class of L{yaner}.
"""

import os
import sys
import logging

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import Gdk

from yaner import SQLSession
from yaner import __version__, __author__
from yaner.Pool import Pool
from yaner.Presentable import Presentable, Category
from yaner.XDG import xdg_open
from yaner.ui.Dialogs import TaskNewDialog
from yaner.ui.Dialogs import CategoryBar, PoolBar
from yaner.ui.PoolTree import PoolModel, PoolView
from yaner.ui.TaskListTree import TaskListModel, TaskListView
from yaner.ui.Misc import load_ui_file
from yaner.ui.Widgets import Box, VERTICAL
from yaner.utils.Logging import LoggingMixin

class Toplevel(Gtk.Window, LoggingMixin):
    """Toplevel window of L{yaner}."""

    _UI_FILE = load_ui_file('ui.xml')
    """The menu and toolbar interfaces, used by L{ui_manager}."""

    def __init__(self):
        """
        Create toplevel window of L{yaner}. The window structure is
        like this:
            - vbox
                - toolbar
                - hpaned
                    - scrolled_window
                        - _pool_view
                    - task_vbox
                        - _task_list_view
        """
        Gtk.Window.__init__(self)
        LoggingMixin.__init__(self)

        self.logger.info('Initializing toplevel window...')

        self._settings = None

        self._popups = None

        # UIManager: Toolbar and menus
        self._action_group = None
        self._ui_manager = None

        self.set_default_size(self.settings.get_uint('width'),
                              self.settings.get_uint('height'))
        if self.settings.get_boolean('maximized'):
            self.maximize()

        self.set_default_icon_name('yaner')

        # The toplevel vbox
        vbox = Box(VERTICAL, 0)
        self.add(vbox)

        # Toolbar
        toolbar = self.ui_manager.get_widget('/toolbar')
        vbox.pack_start(toolbar, expand=False)

        # HPaned: PoolView as left, TaskVBox as right
        hpaned = Gtk.HPaned()
        vbox.pack_start(hpaned)

        # Right pane
        vbox = Box(VERTICAL)
        hpaned.pack2(vbox, True, False)
        self.task_box = vbox

        self._task_list_model = TaskListModel()

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(Gtk.ShadowType.IN)
        scrolled_window.set_size_request(400, -1)
        vbox.pack_end(scrolled_window)

        task_list_view = TaskListView(self._task_list_model)
        task_list_view.set_show_expanders(False)
        task_list_view.set_level_indentation(16)
        task_list_view.expand_all()
        task_list_view.selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        task_list_view.connect('key-press-event',
                               self._on_task_list_view_key_pressed)
        task_list_view.connect('button-press-event',
                               self._on_task_list_view_button_pressed)
        task_list_view.connect('row-activated',
                               self._on_task_list_view_row_activated)
        scrolled_window.add(task_list_view)

        self._task_list_view = task_list_view

        # Left pane
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                   Gtk.PolicyType.NEVER)
        scrolled_window.set_shadow_type(Gtk.ShadowType.IN)
        scrolled_window.set_size_request(180, -1)
        hpaned.pack1(scrolled_window, False, False)

        self._pool_model = PoolModel()

        pool_view = PoolView(self._pool_model)
        pool_view.set_headers_visible(False)
        pool_view.set_show_expanders(False)
        pool_view.set_level_indentation(16)
        pool_view.connect('button-press-event', self._on_pool_view_button_pressed)
        scrolled_window.add(pool_view)

        self._pool_view = pool_view

        pool_view.selection.set_mode(Gtk.SelectionMode.SINGLE)
        pool_view.selection.connect("changed",
                                    self._on_pool_view_selection_changed)

        # Add Pools to the PoolModel
        for pool in SQLSession.query(Pool):
            self._pool_model.add_pool(pool)
        pool_view.expand_all()
        # Select first iter
        pool_view.selection.select_iter(self._pool_model.get_iter_first())

        # Dialogs
        self._task_new_dialog = None
        self._about_dialog = None
        self._category_bar = None
        self._pool_bar = None

        # Status icon
        status_icon = Gtk.StatusIcon(icon_name='yaner')
        status_icon.connect('activate', self._on_status_icon_activated)
        status_icon.connect('popup-menu', self._on_status_icon_popup)

        self.connect('delete-event', self._on_delete_event, status_icon)

        self.logger.info('Toplevel window initialized.')

    @property
    def settings(self):
        """Get the GSettings object."""
        if self._settings is None:
            self._settings = Gio.Settings('com.kissuki.yaner.ui')
        return self._settings

    @property
    def ui_manager(self):
        """Get the UI Manager of L{yaner}."""
        if self._ui_manager is None:
            self.logger.info('Initializing UI Manager...')

            ui_manager = Gtk.UIManager()
            ui_manager.insert_action_group(self.action_group)
            try:
                ui_manager.add_ui_from_file(self._UI_FILE)
            except GObject.GError:
                self.logger.exception("Failed to add ui file to UIManager.")
                SQLSession.close()
                logging.shutdown()
                sys.exit(1)
            else:
                self.logger.info('UI Manager initialized.')
            self._ui_manager = ui_manager
        return self._ui_manager

    @property
    def action_group(self):
        """Get the action group of L{yaner}."""
        if self._action_group is None:
            self.logger.info('Initializing action group...')

            # The actions used by L{action_group}. The members are:
            # name, stock-id, label, accelerator, tooltip, callback
            action_entries = (
                ("task_new", 'gtk-new', _("New Task"), None,
                 None, self._on_task_new),
                ("task_start", 'gtk-media-play', _("Start"), None,
                 None, self._on_task_start),
                ("task_pause", 'gtk-media-pause', _("Pause"), None,
                 None, self._on_task_pause),
                ("task_start_all", 'gtk-media-play', _("Start All"), None,
                 None, self._on_task_start_all),
                ("task_pause_all", 'gtk-media-pause', _("Pause All"), None,
                 None, self._on_task_pause_all),
                ("task_remove", 'gtk-delete', None, None,
                 None, self._on_task_remove),
                ("task_restore", 'gtk-undelete', None, None,
                 None, self._on_task_restore),

                ('category_add', 'gtk-add', _('Add Category'), None,
                 None, self._on_category_add),
                ('category_edit', 'gtk-edit', _('Edit Category'), None,
                 None, self._on_category_edit),
                ('category_remove', 'gtk-delete', _('Remove Category'), None,
                 None, self._on_category_remove),
                ('pool_add', 'gtk-add', _('Add Server'), None,
                 None, self._on_pool_add),
                ('pool_edit', 'gtk-edit', _('Edit Server'), None,
                 None, self._on_pool_edit),
                ('pool_remove', 'gtk-delete', _('Remove Server'), None,
                 None, self._on_pool_remove),
                ('dustbin_empty', 'gtk-delete', _('Empty Dustbin'), None,
                 None, self._on_dustbin_empty),

                ("toggle_hidden", None, _("Show / Hide"), None,
                 None, self._on_toggle_hidden),
                ("about", "gtk-about", None, None, None, self.about),
                ("quit", "gtk-quit", None, None, None, self.destroy),
            )

            action_group = Gtk.ActionGroup("ToplevelActions")
            action_group.add_actions(action_entries, self)

            self.logger.info('Action group initialized.')

            self._action_group = action_group
        return self._action_group

    @property
    def popups(self):
        """Get popup menus, which is a dict."""
        if self._popups is None:
            self.logger.info('Initializing popup menus...')
            get_widget = self.ui_manager.get_widget
            popups = {}
            for popup_name in ('tray', 'pool',
                               'queuing', 'category', 'dustbin',
                               'queuing_task', 'category_task', 'dustbin_task'):
                popups[popup_name] = get_widget('/{}_popup'.format(popup_name))
            self._popups = popups
            self.logger.info('Popup menus initialized.')
        return self._popups

    @property
    def task_new_dialog(self):
        """Get the new task dialog of the window."""
        if self._task_new_dialog is None:
            self._task_new_dialog = TaskNewDialog(self, self._pool_model)
            self._task_new_dialog.set_transient_for(self)
        return self._task_new_dialog

    @property
    def about_dialog(self):
        if self._about_dialog is None:
            about_dialog = Gtk.AboutDialog()
            about_dialog.set_program_name(_('Yaner'))
            about_dialog.set_version(__version__)
            about_dialog.set_logo_icon_name('yaner')
            about_dialog.set_authors((__author__,))
            about_dialog.set_website('https://github.com/iven/Yaner')
            about_dialog.set_copyright('Copyright \u00a9 2010-2011 Iven Hsu')
            about_dialog.set_transient_for(self)
            self._about_dialog = about_dialog
        return self._about_dialog

    @property
    def category_bar(self):
        """The info bar for adding or editing categories."""
        if self._category_bar is None:
            category_bar = CategoryBar(self._pool_view.selected_presentable.pool,
                                       self)
            category_bar.connect('response', self._on_category_bar_response)
            self.task_box.pack_end(category_bar, expand=False)
            self._category_bar = category_bar
        return self._category_bar

    @property
    def pool_bar(self):
        """The info bar for adding or editing pools."""
        if self._pool_bar is None:
            pool_bar = PoolBar()
            pool_bar.connect('response', self._on_pool_bar_response)
            self.task_box.pack_end(pool_bar, expand=False)
            self._pool_bar = pool_bar
        return self._pool_bar

    def _on_status_icon_activated(self, status_icon):
        """When status icon clicked, switch the window visible or hidden."""
        self.logger.debug('Status icon activated.')
        self.action_group.get_action('toggle_hidden').activate()

    def _on_status_icon_popup(self, status_icon, button, activate_time):
        """When status icon right-clicked, show the menu."""
        self.logger.debug('Status icon menu popuped.')
        self.popups['tray'].popup(None, None, None, None, button, activate_time)

    def _on_toggle_hidden(self, action, data):
        """Toggle the toplevel window shown or hidden."""
        if self.get_property('visible'):
            self.hide()
            self.logger.debug('Toplevel window hidden.')
        else:
            self.present()
            self.logger.debug('Toplevel window shown.')

    def _on_delete_event(self, window, event, status_icon):
        """When window close button is clicked, try to hide the window instead
        of quit the application.
        """
        if status_icon.is_embedded():
            self.hide()
            self.logger.debug('Toplevel window hidden.')
            return True
        else:
            return False

    def _on_task_list_view_row_activated(self, treeview, path, column):
        """When task row double clicked, start or pause the task."""
        model = treeview.get_model()
        activating_task = model.get_task(model.get_iter(path))

        presentable = self._pool_view.selected_presentable
        if presentable.TYPE == Presentable.TYPES.QUEUING:
            if activating_task.is_pausable:
                activating_task.pause()
            elif activating_task.is_unpausable or activating_task.is_addable:
                activating_task.start()
        elif presentable.TYPE == Presentable.TYPES.CATEGORY:
            pool = presentable.pool
            if pool.is_local and not activating_task.has_bittorrent:
                path = os.path.join(activating_task.options['dir'],
                                    activating_task.options['out'])
                self.logger.info('Opening file {}...'.format(path))
                xdg_open([path])

    def _on_task_list_view_key_pressed(self, treeview, event):
        if event.keyval == Gdk.KEY_Delete:
            self._on_task_remove()

    def _on_task_list_view_button_pressed(self, treeview, event):
        """Popup menu when necessary."""
        selection = treeview.get_selection()
        (model, paths) = selection.get_selected_rows()
        current_path = treeview.get_path_at_pos(event.x, event.y)
        if current_path is None:
            selection.unselect_all()
            return True

        if event.button == 3:
            # If the clicked row is not selected, select it only
            if current_path is not None and current_path[0] not in paths:
                selection.unselect_all()
                selection.select_path(current_path[0])

            popup_dict = {Presentable.TYPES.QUEUING: 'queuing_task',
                          Presentable.TYPES.CATEGORY: 'category_task',
                          Presentable.TYPES.DUSTBIN: 'dustbin_task',
                         }
            popup_menu = self.popups[popup_dict[model.presentable.TYPE]]
            popup_menu.popup(None, None, None, None, event.button, event.time)
            return True
        return False

    def _on_pool_view_button_pressed(self, treeview, event):
        """Popup menu when necessary."""
        selection = treeview.get_selection()
        (model, iter_) = selection.get_selected()
        current_path = treeview.get_path_at_pos(event.x, event.y)

        if event.button == 3:
            if current_path is None:
                self.popups['pool'].popup(None, None, None, None,
                                          event.button, event.time)
                return True

            # If the clicked row is not selected, select it
            if current_path[0] != model.get_path(iter_):
                selection.select_path(current_path[0])

            popup_dict = {Presentable.TYPES.QUEUING: 'queuing',
                          Presentable.TYPES.CATEGORY: 'category',
                          Presentable.TYPES.DUSTBIN: 'dustbin',
                         }
            popup_menu = self.popups[popup_dict[treeview.selected_presentable.TYPE]]
            popup_menu.popup(None, None, None, None, event.button, event.time)
            return True
        return False

    def _on_pool_view_selection_changed(self, selection):
        """
        Pool view tree selection changed signal callback.
        Update the task list model.
        """
        presentable = self._pool_view.selected_presentable
        if presentable is not None:
            self._task_list_model.presentable = presentable

    def _on_task_new(self, action, data):
        """When task new action is activated, call the task new dialog."""
        self.task_new_dialog.run()

    def _on_task_start(self, action, data):
        """When task start button clicked, start or unpause the task."""
        for task in self._task_list_view.selected_tasks:
            task.start()

    def _on_task_pause(self, action, data):
        """When task pause button clicked, pause the task."""
        for task in self._task_list_view.selected_tasks:
            task.pause()

    def _on_task_start_all(self, action, data):
        """Start or unpause all the tasks in the selected pool."""
        presentable = self._pool_view.selected_presentable
        if presentable is None or presentable.TYPE != Presentable.TYPES.QUEUING:
            pools = SQLSession.query(Pool)
        else:
            pools = [presentable.pool]

        for pool in pools:
            for task in pool.queuing.tasks:
                task.start()

    def _on_task_pause_all(self, action, data):
        """Pause all the tasks in the selected pool."""
        presentable = self._pool_view.selected_presentable
        if presentable is None or presentable.TYPE != Presentable.TYPES.QUEUING:
            pools = SQLSession.query(Pool)
        else:
            pools = [presentable.pool]

        for pool in pools:
            for task in pool.queuing.tasks:
                task.pause()

    def _on_task_remove(self, action=None, data=None):
        """When task remove button clicked, remove the task."""
        tasks = self._task_list_view.selected_tasks
        if not tasks:
            return

        if self._pool_view.selected_presentable.TYPE == Presentable.TYPES.DUSTBIN:
            dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                       Gtk.MessageType.WARNING,
                                       Gtk.ButtonsType.YES_NO,
                                       _('Are you sure to remove these tasks?'),
                                      )
            response = dialog.run()
            dialog.destroy()
            if response == Gtk.ResponseType.YES:
                for task in tasks:
                    task.remove()
        else:
            for task in tasks:
                task.trash()

    def _on_task_restore(self, action, data):
        """When task is removed, restore the task."""
        for task in self._task_list_view.selected_tasks:
            task.restore()

    def do_configure_event(self, event):
        """When window size changed, save it in GSettings."""
        settings = self.settings
        if not settings.get_boolean('maximized'):
            settings.set_uint('width', event.width)
            settings.set_uint('height', event.height)

        Gtk.Window.do_configure_event(self, event)

    def do_window_state_event(self, event):
        """When window maximized, save it in GSettings."""
        maximized = event.new_window_state & Gdk.WindowState.MAXIMIZED
        self.settings.set_boolean('maximized', maximized)

        Gtk.Window.do_window_state_event(self, event)

    def _on_dustbin_empty(self, action, data):
        """Empty dustbin."""
        if self._pool_view.selected_presentable.TYPE == Presentable.TYPES.DUSTBIN:
            self._task_list_view.get_selection().select_all()
            self.action_group.get_action('task_remove').activate()

    def _on_category_add(self, action, data):
        """Add category."""
        presentable = self._pool_view.selected_presentable
        self.category_bar.update(presentable.pool)
        self.category_bar.show_all()

    def _on_category_edit(self, action, data):
        """Edit category."""
        presentable = self._pool_view.selected_presentable
        self.category_bar.update(presentable.pool, presentable)
        self.category_bar.show_all()

    def _on_category_remove(self, action, data):
        """Remove category."""
        category = self._pool_view.selected_presentable
        pool = category.pool
        if category is pool.default_category:
            dialog = Gtk.MessageDialog(
                self, Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.CLOSE,
                _('The default category should not be removed.'),
                )
        else:
            dialog = Gtk.MessageDialog(
                self, Gtk.DialogFlags.MODAL,
                Gtk.MessageType.WARNING,
                Gtk.ButtonsType.YES_NO,
                _('Are you sure to remove the category "{}"?\nAll tasks '
                  'in the category will be moved to the default category.'
                 ).format(category.name),
                )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            # Move all tasks to default category
            for task in category.tasks:
                task.category = pool.default_category
                pool.default_category.add_task(task)
            # Remove the category iter
            self._pool_model.remove_presentable(category)
            SQLSession.delete(category)
            SQLSession.commit()

    def _on_category_bar_response(self, info_bar, response_id):
        """When category_bar responsed, create or edit category."""
        if response_id != Gtk.ResponseType.OK:
            info_bar.hide()
            return

        category = info_bar.category
        pool = info_bar.pool
        widgets = info_bar.widgets

        name = widgets['name'].get_text().strip()
        directory = widgets['directory'].get_text().strip()

        if not name:
            widgets['name'].set_placeholder_text(_('Required'))
            return
        if not directory:
            widgets['directory'].set_placeholder_text(_('Required'))
            return

        if category is None:
            category = Category(name=name, directory=directory, pool=pool)
            self._pool_model.add_presentable(category, insert=True)
        else:
            category.name=name
            category.directory=directory
            SQLSession.commit()
        info_bar.hide()

    def _on_pool_add(self, action, data):
        """Add pool."""
        self.pool_bar.update(None)
        self.pool_bar.show_all()

    def _on_pool_edit(self, action, data):
        """Edit pool."""
        presentable = self._pool_view.selected_presentable
        self.pool_bar.update(presentable.pool)
        self.pool_bar.show_all()

    def _on_pool_remove(self, action, data):
        """Remove pool."""
        queuing = self._pool_view.selected_presentable
        pool = queuing.pool
        if pool.is_local:
            dialog = Gtk.MessageDialog(
                self, Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.CLOSE,
                _('The local server should not be removed.'),
                )
        else:
            dialog = Gtk.MessageDialog(
                self, Gtk.DialogFlags.MODAL,
                Gtk.MessageType.WARNING,
                Gtk.ButtonsType.YES_NO,
                _('Are you sure to remove the server "{}"?\nAll tasks '
                  'in the server will be <b>removed!</b>'
                 ).format(pool.name),
                use_markup=True
                )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            # Select the local pool, in order to remove the selected pool
            local_pool = SQLSession.query(Pool).filter(Pool.is_local == True)[0]
            iter_ = self._pool_model.get_iter_for_presentable(local_pool.queuing)
            self._pool_view.selection.select_iter(iter_)
            # Remove the category iter
            self._pool_model.remove_pool(pool)
            SQLSession.delete(pool)
            SQLSession.commit()

    def _on_pool_bar_response(self, info_bar, response_id):
        """When pool bar responsed, create or edit pool."""
        if response_id != Gtk.ResponseType.OK:
            info_bar.hide()
            return

        pool = info_bar.pool
        widgets = info_bar.widgets
        props = {}

        for (prop, widget) in widgets.items():
            props[prop] = widget.get_text().strip()

        for prop in ('name', 'host', 'port'):
            if not props[prop]:
                widgets[prop].set_placeholder_text(_('Required'))
                return

        if pool is None:
            pool = Pool(**props)
            self._pool_model.add_pool(pool)
            self._pool_view.expand_all()
        else:
            pool.name = props['name']
            pool.host = props['host']
            pool.port = props['port']
            pool.user = props['user']
            pool.passwd = props['passwd']
            SQLSession.commit()

        info_bar.hide()

    def about(self, *args, **kwargs):
        """Show about dialog."""
        self.about_dialog.run()
        self.about_dialog.hide()

    def destroy(self, *args, **kwargs):
        """Destroy toplevel window and quit the application."""
        Gtk.Window.destroy(self)
        self.logger.debug('Window destroyed.')

