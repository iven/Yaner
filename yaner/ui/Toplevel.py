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

import sys
import logging

from gi.repository import Gtk
from gi.repository import GObject
from functools import partial

from yaner import SQLSession
from yaner import __version__, __author__
from yaner.Pool import Pool
from yaner.Task import Task
from yaner.Presentable import Presentable
from yaner.ui.Dialogs import TaskNewDialog
from yaner.ui.PoolTree import PoolModel, PoolView
from yaner.ui.TaskListTree import TaskListModel, TaskListView
from yaner.ui.Misc import load_ui_file
from yaner.utils.Logging import LoggingMixin

class Toplevel(Gtk.Window, LoggingMixin):
    """Toplevel window of L{yaner}."""

    _UI_FILE = load_ui_file('ui.xml')
    """The menu and toolbar interfaces, used by L{ui_manager}."""

    def __init__(self, config):
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

        self.logger.info(_('Initializing toplevel window...'))

        self._config = config

        self.set_size_request(650, 450)

        # The toplevel vbox
        vbox = Gtk.VBox(False, 0)
        self.add(vbox)

        # UIManager: Toolbar and menus
        self._action_group = None
        self._ui_manager = None

        toolbar = self.ui_manager.get_widget('/toolbar')
        vbox.pack_start(toolbar, False, False, 0)

        self._popups = None

        # HPaned: PoolView as left, TaskVBox as right
        hpaned = Gtk.HPaned()
        vbox.pack_start(hpaned, True, True, 0)

        # Right pane
        task_vbox = Gtk.VBox(False, 12)
        hpaned.add2(task_vbox)

        self._task_list_model = TaskListModel()

        task_list_view = TaskListView(self._task_list_model)
        task_list_view.set_show_expanders(False)
        task_list_view.set_level_indentation(16)
        task_list_view.expand_all()
        task_list_view.selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        task_list_view.connect('button-press-event', self._on_task_list_view_button_pressed)

        self._task_list_view = task_list_view

        task_vbox.pack_start(self._task_list_view, True, True, 0)

        # Left pane
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                Gtk.PolicyType.NEVER)
        scrolled_window.set_shadow_type(Gtk.ShadowType.IN)
        scrolled_window.set_size_request(80, -1)
        hpaned.pack1(scrolled_window, True, True)

        self._pool_model = PoolModel()

        pool_view = PoolView(self._pool_model)
        pool_view.set_size_request(200, -1)
        pool_view.set_headers_visible(False)
        pool_view.set_show_expanders(False)
        pool_view.set_level_indentation(16)

        self._pool_view = pool_view

        pool_view.selection.set_mode(Gtk.SelectionMode.SINGLE)
        pool_view.selection.connect("changed",
                self.on_pool_view_selection_changed)

        # Add Pools to the PoolModel
        for pool in SQLSession.query(Pool):
            self._pool_model.add_pool(pool)
        pool_view.expand_all()
        # Select first iter
        pool_view.selection.select_iter(
                self._pool_model.get_iter_first())

        scrolled_window.add(self._pool_view)

        # Dialogs
        self._task_new_dialog = TaskNewDialog()
        self._task_new_dialog.widgets['dialog'].set_transient_for(self)

        self._about_dialog = None

        # Status icon
        status_icon = Gtk.StatusIcon(stock='gtk-apply')
        status_icon.connect('activate', self._on_status_icon_activated)
        status_icon.connect('popup-menu', self._on_status_icon_popup)

        self.connect('delete-event', self._on_delete_event, status_icon)

        self.logger.info(_('Toplevel window initialized.'))

    @property
    def ui_manager(self):
        """Get the UI Manager of L{yaner}."""
        if self._ui_manager is None:
            self.logger.info(_('Initializing UI Manager...'))

            ui_manager = Gtk.UIManager()
            ui_manager.insert_action_group(self.action_group)
            try:
                ui_manager.add_ui_from_file(self._UI_FILE)
            except GObject.GError:
                self.logger.exception(_("Failed to add ui file to UIManager."))
                logging.shutdown()
                sys.exit(1)
            else:
                self.logger.info(_('UI Manager initialized.'))
            self._ui_manager = ui_manager
        return self._ui_manager

    @property
    def action_group(self):
        """Get the action group of L{yaner}."""
        if self._action_group is None:
            self.logger.info(_('Initializing action group...'))

            # The actions used by L{action_group}. The members are:
            # name, stock-id, label, accelerator, tooltip, callback
            action_entries = (
                ("task_new", 'gtk-add', _("New Task"), None, None,
                    partial(self.on_task_new, task_type = Task.TYPES.NORMAL)),
                ("task_new_normal", 'gtk-add', _("HTTP/FTP/BT Magnet"), None, None,
                    partial(self.on_task_new, task_type = Task.TYPES.NORMAL)),
                ("task_new_bt", 'gtk-add', _("BitTorrent"), None, None,
                    partial(self.on_task_new, task_type = Task.TYPES.BT)),
                ("task_new_ml", 'gtk-add', _("Metalink"), None, None,
                    partial(self.on_task_new, task_type = Task.TYPES.ML)),
                ("task_start", 'gtk-media-play', _("Start"), None, None,
                    self.on_task_start),
                ("task_pause", 'gtk-media-pause', _("Pause"), None, None,
                    self.on_task_pause),
                ("task_start_all", 'gtk-media-play', _("Start All"), None, None,
                    self.on_task_start_all),
                ("task_pause_all", 'gtk-media-pause', _("Pause All"), None, None,
                    self.on_task_pause_all),
                ("task_remove", 'gtk-delete', _("Remove"), None, None,
                    self.on_task_remove),
                ("task_restore", 'gtk-undelete', _("Restore"), None, None,
                    self.on_task_restore),
                ("toggle_hidden", None, _("Show / Hide"), None, None,
                    self._on_toggle_hidden),
                ("about", "gtk-about", None, None, None, self.about),
                ("quit", "gtk-quit", None, None, None, self.destroy),
            )

            action_group = Gtk.ActionGroup("ToplevelActions")
            action_group.add_actions(action_entries, self)

            self.logger.info(_('Action group initialized.'))

            self._action_group = action_group
        return self._action_group

    @property
    def popups(self):
        """Get popup menus, which is a dict."""
        if self._popups is None:
            get_widget = self.ui_manager.get_widget
            popups = {}
            for popup_name in ('tray', 'queuing_task', 'category_task',
                               'dustbin_task'):
                popups[popup_name] = get_widget('/{}_popup'.format(popup_name))
            self._popups = popups
        return self._popups

    @property
    def task_new_dialog(self):
        """Get the new task dialog of the window."""
        return self._task_new_dialog

    @property
    def about_dialog(self):
        if self._about_dialog is None:
            about_dialog = Gtk.AboutDialog()
            about_dialog.set_program_name(_('Yaner'))
            about_dialog.set_version(__version__)
            about_dialog.set_authors((__author__,))
            about_dialog.set_website('https://github.com/iven/Yaner')
            about_dialog.set_copyright('Copyright \u00a9 2010-2011 Iven Hsu')
            about_dialog.set_transient_for(self)
            self._about_dialog = about_dialog
        return self._about_dialog

    @property
    def config(self):
        """Get the global configuration of the application."""
        return self._config

    def _on_status_icon_activated(self, status_icon):
        """When status icon clicked, switch the window visible or hidden."""
        self.action_group.get_action('toggle_hidden').activate()

    def _on_status_icon_popup(self, status_icon, button, activate_time):
        """When status icon right-clicked, show the menu."""
        self.popups['tray'].popup(None, None, None, None, button, activate_time)

    def _on_toggle_hidden(self, action, user_data):
        """Toggle the toplevel window shown or hidden."""
        if self.get_property('visible'):
            self.hide()
        else:
            self.present()

    def _on_delete_event(self, window, event, status_icon):
        """When window close button is clicked, try to hide the window instead
        of quit the application.
        """
        if status_icon.is_embedded():
            self.hide()
            return True
        else:
            return False

    def _on_task_list_view_button_pressed(self, treeview, event):
        """Popup menu when necessary."""
        # If the clicked row is not selected, select it only
        selection = treeview.get_selection()
        (model, paths) = selection.get_selected_rows()
        current_path = treeview.get_path_at_pos(event.x, event.y)
        if current_path is None:
            selection.unselect_all()

        if event.button == 3:
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

    def on_pool_view_selection_changed(self, selection):
        """
        Pool view tree selection changed signal callback.
        Update the task list model.
        """
        self._task_list_model.presentable = self._pool_view.selected_presentable

    def on_task_new(self, action, user_data, task_type):
        """When task new action is activated, call the task new dialog."""
        self.task_new_dialog.run_dialog(task_type)

    def on_task_start(self, action, user_data):
        """When task start button clicked, start or unpause the task."""
        for task in self._task_list_view.selected_tasks:
            task.start()

    def on_task_pause(self, action, user_data):
        """When task pause button clicked, pause the task."""
        for task in self._task_list_view.selected_tasks:
            task.pause()

    def on_task_start_all(self, action, user_data):
        """Start or unpause all the tasks."""
        for pool in SQLSession.query(Pool):
            for task in pool.queuing.tasks:
                task.start()

    def on_task_pause_all(self, action, user_data):
        """Pause all the tasks."""
        for pool in SQLSession.query(Pool):
            for task in pool.queuing.tasks:
                task.pause()

    def on_task_remove(self, action, user_data):
        """When task remove button clicked, remove the task."""
        tasks = self._task_list_view.selected_tasks
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

    def on_task_restore(self, action, user_data):
        """When task is removed, restore the task."""
        for task in self._task_list_view.selected_tasks:
            task.restore()

    def about(self, *args, **kwargs):
        """Show about dialog."""
        self.about_dialog.run()
        self.about_dialog.hide()

    def destroy(self, *args, **kwargs):
        """Destroy toplevel window and quit the application."""
        Gtk.Window.destroy(self)

