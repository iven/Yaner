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
This module contains the toplevel window class of L{yaner}.
"""

import gtk
import glib
import gobject
import os
import sys
import logging
from functools import partial

from yaner.Pool import Pool
from yaner.Task import Task
from yaner.ui.Constants import UI_DIR
from yaner.ui.Dialogs import TaskNewDialog
from yaner.ui.PoolTree import PoolModel, PoolView
from yaner.ui.TaskListTree import TaskListModel, TaskListView
from yaner.utils.Logging import LoggingMixin

class Toplevel(gtk.Window, LoggingMixin):
    """Toplevel window of L{yaner}."""

    _UI_FILE = os.path.join(UI_DIR, "ui.xml")
    """The menu and toolbar interfaces, used by L{ui_manager}."""

    def __init__(self, bus, config):
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
        gtk.Window.__init__(self)
        LoggingMixin.__init__(self)

        self.logger.info(_('Initializing toplevel window...'))

        self._config = config

        self.set_default_size(800, 600)

        # The toplevel vbox
        vbox = gtk.VBox(False, 0)
        self.add(vbox)

        # UIManager: Toolbar and menus
        self._action_group = None
        self._ui_manager = None

        toolbar = self.ui_manager.get_widget('/toolbar')
        vbox.pack_start(toolbar, False, False, 0)

        # HPaned: PoolView as left, TaskVBox as right
        hpaned = gtk.HPaned()
        vbox.pack_start(hpaned, True, True, 0)

        # Right pane
        task_vbox = gtk.VBox(False, 12)
        hpaned.add2(task_vbox)

        self._task_list_model = TaskListModel()

        task_list_view = TaskListView(self._task_list_model)
        task_list_view.set_show_expanders(False)
        task_list_view.set_level_indentation(16)
        task_list_view.expand_all()
        task_list_view.selection.set_mode(gtk.SELECTION_MULTIPLE)

        self._task_list_view = task_list_view

        task_vbox.pack_start(self._task_list_view, True, True, 0)

        # Left pane
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        hpaned.add1(scrolled_window)

        self._pool_model = PoolModel()

        # Add Pools to the PoolModel
        for pool in Pool.select():
            self._add_pool(pool)

        pool_view = PoolView(self._pool_model)
        pool_view.set_size_request(200, -1)
        pool_view.set_headers_visible(False)
        pool_view.set_show_expanders(False)
        pool_view.set_level_indentation(16)
        pool_view.expand_all()

        self._pool_view = pool_view

        pool_view.selection.set_mode(gtk.SELECTION_SINGLE)
        pool_view.selection.connect("changed",
                self.on_pool_view_selection_changed)
        pool_view.selection.select_iter(
                self._pool_model.get_iter_first())

        scrolled_window.add(self._pool_view)

        # Dialogs
        self._task_new_dialog = TaskNewDialog(bus)

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
    def config(self):
        """Get the global configuration of the application."""
        return self._config

    def _init_action_group(self):
        """Initialize the action group."""
        self.logger.info(_('Initializing action group...'))

        # The actions used by L{action_group}. The members are:
        # name, stock-id, label, accelerator, tooltip, callback
        action_entries = (
                ("file", None, _("File")),
                ("task_new", "gtk-add"),
                ("task_new_normal", None, _("HTTP/FTP/BT Magnet"), None, None,
                    partial(self.on_task_new, task_type = Task.TYPES.NORMAL)),
                ("task_new_bt", None, _("BitTorrent"), None, None,
                    partial(self.on_task_new, task_type = Task.TYPES.BT)),
                ("task_new_ml", None, _("Metalink"), None, None,
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

        action_group = gtk.ActionGroup("ToplevelActions")
        action_group.add_actions(action_entries, self)

        # Hack for the MenuToolButton
        gobject.type_register(MenuToolAction)
        MenuToolAction.set_tool_item_type(gtk.MenuToolButton)
        menu_tool_action = MenuToolAction(
                "task_new_tool_menu", None, None, 'gtk-add')
        action_group.add_action(menu_tool_action)

        self.logger.info(_('Action group initialized.'))

        return action_group

    def _init_ui_manager(self):
        """Initialize the UIManager, including menus and toolbar."""
        self.logger.info(_('Initializing UI Manager...'))

        ui_manager = gtk.UIManager()
        ui_manager.insert_action_group(self.action_group)
        try:
            ui_manager.add_ui_from_file(self._UI_FILE)
        except glib.GError:
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
        pass

    def on_task_pause(self, action, user_data):
        for task in self._task_list_view.selected_tasks:
            task.pause()

    def on_task_remove(self, action, user_data):
        for task in self._task_list_view.selected_tasks:
            task.remove()

    def update(self):
        """Update the window."""
        pass

    def about(self, *args, **kwargs):
        pass

    def destroy(self, *args, **kwargs):
        """Destroy toplevel window and quit the application."""
        gtk.Window.destroy(self)

class MenuToolAction(gtk.Action):
    """
    C{gtk.Action} used by C{gtk.MenuToolButton}.
    """
    __gtype_name__ = "MenuToolAction"

