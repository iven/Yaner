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
This module contains the infobar classes of L{yaner}.
"""

from gi.repository import Gtk

from yaner.ui.Widgets import RightAlignedLabel, FileChooserEntry, Grid

class CategoryBar(Gtk.InfoBar):
    """A InfoBar used to adding or editing categories."""
    def __init__(self, pool, parent):
        Gtk.InfoBar.__init__(self, message_type=Gtk.MessageType.OTHER)

        widgets = {}
        content_area = self.get_content_area()

        grid = Grid()
        content_area.pack_start(grid, True, True, 0)

        label = RightAlignedLabel(_('Category Name:'))
        grid.attach(label, 0, 0)

        entry = Gtk.Entry(hexpand=True)
        grid.attach(entry, 1, 0)
        widgets['name'] = entry

        label = RightAlignedLabel(_('Default directory:'))
        grid.attach(label, 0, 1)

        entry = FileChooserEntry(_('Select default directory'), parent,
                                 Gtk.FileChooserAction.SELECT_FOLDER,
                                 hexpand=True
                                )
        grid.attach(entry, 1, 1)
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

        grid = Grid()
        content_area.pack_start(grid, True, True, 0)

        label = RightAlignedLabel(_('Server Name:'))
        grid.attach(label, 0, 0)

        entry = Gtk.Entry(hexpand=True)
        grid.attach(entry, 1, 0)
        widgets['name'] = entry

        label = RightAlignedLabel(_('IP Address:'))
        grid.attach(label, 0, 1)

        entry = Gtk.Entry(hexpand=True)
        grid.attach(entry, 1, 1)
        widgets['host'] = entry

        label = RightAlignedLabel(_('Port:'))
        grid.attach(label, 0, 2)

        entry = Gtk.Entry(hexpand=True)
        grid.attach(entry, 1, 2)
        widgets['port'] = entry

        label = RightAlignedLabel(_('User:'))
        grid.attach(label, 0, 3)

        entry = Gtk.Entry(hexpand=True)
        grid.attach(entry, 1, 3)
        widgets['user'] = entry

        label = RightAlignedLabel(_('Password:'))
        grid.attach(label, 0, 4)

        entry = Gtk.Entry(hexpand=True)
        grid.attach(entry, 1, 4)
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

