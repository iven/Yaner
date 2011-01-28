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
from gettext import gettext as _
from os.path import join as _join

from Constants import UI_DIR

class Toplevel(gtk.Window):
    """Toplevel window of L{yaner}."""

    _ui_file = _join(UI_DIR, "ui.xml")
    """The menu and toolbar interfaces, used by L{ui_manager}."""

    _action_entries = (
            ("file", None, _("File")),
            ("task_new", "gtk-add"),
            ("task_new_normal", None, _("HTTP/FTP/BT Magnet")),
            ("task_new_bt", None, _("BitTorrent")),
            ("task_new_ml", None, _("Metalink")),
            ("quit", "gtk-quit"),
    )
    """The actions used by L{action_group}."""

    def __init__(self):
        """Create toplevel window of L{yaner}."""
        gtk.Window.__init__(self)

        self.set_default_size(800, 600)

        vbox = gtk.VBox(False, 0)
        self.add(vbox)

        self._action_group = gtk.ActionGroup("ToplevelActions")
        self._action_group.add_actions(self._action_entries, self)
        self._ui_manager = self._init_ui_manager()
        menubar = self._ui_manager.get_widget('/menubar')
        vbox.pack_start(menubar, False, False, 0)

    @property
    def ui_manager(self):
        """Get the UI Manager of L{yaner}."""
        return self._ui_manager

    @property
    def action_group(self):
        """Get the action group of L{yaner}."""
        return self._action_group

    def _init_ui_manager(self):
        """Initialize L{ui_manager}."""
        ui = gtk.UIManager()
        ui.insert_action_group(self.action_group)
        ui.add_ui_from_file(self._ui_file)
        return ui

