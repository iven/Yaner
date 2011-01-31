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
import sys
import logging
from gettext import gettext as _
from os.path import join as _join

from Constants import UI_DIR
from ..utils.Logging import LoggingMixin

class Toplevel(gtk.Window, LoggingMixin):
    """Toplevel window of L{yaner}."""

    _ui_file = _join(UI_DIR, "ui.xml")
    """The menu and toolbar interfaces, used by L{ui_manager}."""

    def __init__(self):
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

        self.logger.info(_('Initializing toplevel window.'))

        self.set_default_size(800, 600)

        # The toplevel vbox
        vbox = gtk.VBox(False, 0)
        self.add(vbox)

        # UIManager: Toolbar and menus
        self._action_group = self._init_action_group()
        self._ui_manager = self._init_ui_manager()
        if self._ui_manager is None:
            return

        menubar = self._ui_manager.get_widget('/menubar')
        vbox.pack_start(menubar, False, False, 0)

        toolbar = self._ui_manager.get_widget('/toolbar')
        vbox.pack_start(toolbar, False, False, 0)

        # HPaned: PoolView as left, TaskVBox as right
        hpaned = gtk.HPaned()
        vbox.pack_start(hpaned, True, True, 0)

        # Left pane
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        hpaned.add1(scrolled_window)

        self._pool_view = gtk.TreeView()
        self._pool_view.set_size_request(200, -1)
        scrolled_window.add(self._pool_view)

        # Right pane
        task_vbox = gtk.VBox(False, 12)
        hpaned.add2(task_vbox)

        self.logger.info(_('Toplevel window initialized.'))

    @property
    def ui_manager(self):
        """Get the UI Manager of L{yaner}."""
        return self._ui_manager

    @property
    def action_group(self):
        """Get the action group of L{yaner}."""
        return self._action_group

    def _init_action_group(self):
        """Initialize the action group."""
        # The actions used by L{action_group}. The members are:
        # name, stock-id, label, accelerator, tooltip, callback
        action_entries = (
                ("file", None, _("File")),
                ("task_new", "gtk-add"),
                ("task_new_normal", None, _("HTTP/FTP/BT Magnet")),
                ("task_new_bt", None, _("BitTorrent")),
                ("task_new_ml", None, _("Metalink")),
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

        return action_group

    def _init_ui_manager(self):
        """Initialize the UIManager, including menus and toolbar."""
        ui_manager = gtk.UIManager()
        ui_manager.insert_action_group(self.action_group)
        try:
            ui_manager.add_ui_from_file(self._ui_file)
        except glib.GError as e:
            self.logger.exception(_("Failed to add ui file to UIManager."))
            logging.shutdown()
            sys.exit(1)
        else:
            return ui_manager

    def destroy(self, *args, **kwargs):
        """Destroy toplevel window and quit the application."""
        gtk.Window.destroy(self)

class MenuToolAction(gtk.Action):
    __gtype_name__ = "MenuToolAction"

