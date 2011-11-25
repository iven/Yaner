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
from yaner.ui.Dialogs import TaskNewDialog
from yaner.ui.PoolTree import PoolModel, PoolView
from yaner.ui.TaskListTree import TaskListModel, TaskListView
from yaner.utils.XDG import load_first_data
from yaner.utils.Logging import LoggingMixin

class Toplevel(Gtk.Window, LoggingMixin):
    """Toplevel window of L{yaner}."""

    _UI_FILE = load_first_data('yaner', 'ui', 'ui.xml')
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

        # Add Pools to the PoolModel
        for pool in SQLSession.query(Pool):
            self._add_pool(pool)

        pool_view = PoolView(self._pool_model)
        pool_view.set_size_request(200, -1)
        pool_view.set_headers_visible(False)
        pool_view.set_show_expanders(False)
        pool_view.set_level_indentation(16)
        pool_view.expand_all()

        self._pool_view = pool_view

        pool_view.selection.set_mode(Gtk.SelectionMode.SINGLE)
        pool_view.selection.connect("changed",
                self.on_pool_view_selection_changed)
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

        self.connect('delete-event', self._on_delete_event, status_icon)

        self.logger.info(_('Toplevel window initialized.'))

    @property
    def ui_manager(self):
        """Get the UI Manager of L{yaner}."""
        if self._ui_manager is None:
            self._ui_manager = self._init_ui_manager()
        return self._ui_manager

    @property
    def action_group(self):
        """Get the action group of L{yaner}."""
        if self._action_group is None:
            self._action_group = self._init_action_group()
        return self._action_group

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

    def _init_action_group(self):
        """Initialize the action group."""
        self.logger.info(_('Initializing action group...'))

        # The actions used by L{action_group}. The members are:
        # name, stock-id, label, accelerator, tooltip, callback
        action_entries = (
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
                ("task_remove", 'gtk-delete', _("Remove"), None, None,
                    self.on_task_remove),
                ("about", "gtk-about", None, None, None, self.about),
                ("quit", "gtk-quit", None, None, None, self.destroy),
        )

        action_group = Gtk.ActionGroup("ToplevelActions")
        action_group.add_actions(action_entries, self)

        self.logger.info(_('Action group initialized.'))

        return action_group

    def _init_ui_manager(self):
        """Initialize the UIManager, including menus and toolbar."""
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
            return ui_manager

    def _add_pool(self, pool):
        """
        Initialize pools for the application.
        A pool is an alias for an aria2 server.
        """
        self.logger.debug(_('Adding pool {0}...').format(pool.name))
        pool.connect('presentable-added', self.update)
        pool.connect('presentable-removed', self.update)
        self._pool_model.add_pool(pool)

    def _on_status_icon_activated(self, status_icon):
        """When status icon clicked, switch the window visible or hidden."""
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

    def on_task_remove(self, action, user_data):
        """When task remove button clicked, remove the task."""
        for task in self._task_list_view.selected_tasks:
            task.remove()

    def update(self):
        """Update the window."""
        pass

    def about(self, *args, **kwargs):
        """Show about dialog."""
        self.about_dialog.run()
        self.about_dialog.hide()

    def destroy(self, *args, **kwargs):
        """Destroy toplevel window and quit the application."""
        Gtk.Window.destroy(self)

