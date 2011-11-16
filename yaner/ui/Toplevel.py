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
                - menubar
                - hpaned
                    - scrolled_window
                        - _pool_view
                    - task_vbox
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

        menubar = self.ui_manager.get_widget('/menubar')
        vbox.pack_start(menubar, False, False, 0)

        toolbar = self.ui_manager.get_widget('/toolbar')
        vbox.pack_start(toolbar, False, False, 0)

        # HPaned: PoolView as left, TaskVBox as right
        hpaned = gtk.HPaned()
        vbox.pack_start(hpaned, True, True, 0)

        # Right pane
        task_vbox = gtk.VBox(False, 12)
        hpaned.add2(task_vbox)

        self._task_list_model = TaskListModel()
        self._task_list_view = TaskListView(self._task_list_model)
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

        self._pool_view = PoolView(self._pool_model)
        self._pool_view.set_size_request(200, -1)
        self._pool_view.expand_all()
        scrolled_window.add(self._pool_view)

        self._pool_view.selection.connect("changed",
                self.on_pool_view_selection_changed)
        self._pool_view.selection.select_iter(
                self._pool_model.get_iter_first())

        # Dialogs
        self._task_new_dialog = TaskNewDialog(bus)

        # Status icon
        status_icon = gtk.status_icon_new_from_stock('gtk-apply')
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
        pool.connect('status-changed', self.on_pool_status_changed)
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

    def on_pool_status_changed(self, pool):
        """
        Pool status-changed signal callback. Remove the pool and update
        L{PoolModel}.
        @TODO: Remove the pool, or fold it?
        @TODO: Is this necessary?
        """
        pass

    def on_pool_view_selection_changed(self, selection):
        """
        Pool view tree selection changed signal callback.
        Update the task list model.
        """
        (model, iter_) = selection.get_selected()
        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)
        self._task_list_model.presentable = presentable

    def on_task_new(self, action, user_data, task_type):
        """When task new action is activated, call the task new dialog."""
        self.task_new_dialog.run_dialog(task_type)

    def update(self):
        """Update the window."""
        pass

    def destroy(self, *args, **kwargs):
        """Destroy toplevel window and quit the application."""
        gtk.Window.destroy(self)

class MenuToolAction(gtk.Action):
    """
    C{gtk.Action} used by C{gtk.MenuToolButton}.
    """
    __gtype_name__ = "MenuToolAction"

