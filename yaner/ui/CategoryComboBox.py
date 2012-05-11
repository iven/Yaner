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

"""This module contains the combo box classes of the C{Gtk.ComboBox} in the
new task dialog.
"""

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Pango

from yaner.Presentable import Presentable
from yaner.ui.PoolTree import PoolModel
from yaner.utils.Logging import LoggingMixin

class CategoryFilterModel(Gtk.TreeModelFilter, LoggingMixin):
    """The data used by L{CategoryComboBox}.
    It filters L{yaner.ui.PoolTree.PoolModel}, and only displays Pools and
    Categories.
    """
    def __init__(self, child_model):
        Gtk.TreeModelFilter.__init__(self, child_model=child_model)
        self.set_visible_func(self._category_visible_func, None)

    def _category_visible_func(self, model, iter_, data):
        """Show categorys of the selected pool in the combo box."""
        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)
        return (presentable is not None and 
                presentable.TYPE in (Presentable.TYPES.CATEGORY,
                                     Presentable.TYPES.QUEUING)
               )

class CategoryComboBox(Gtk.ComboBox):
    """A ComboBox for selecting the category of the task."""
    def __init__(self, model, parent):
        Gtk.ComboBox.__init__(self, model=model)

        self._active_category = None

        renderer = Gtk.CellRendererPixbuf()
        self.pack_start(renderer, False)
        self.set_cell_data_func(renderer, self._pixbuf_data_func, None)

        renderer = Gtk.CellRendererText()
        self.pack_start(renderer, True)
        self.set_cell_data_func(renderer, self._markup_data_func, None)

        self.connect('changed', self._on_changed)

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

    def _on_changed(self, category_cb):
        """When category combo box changed, update the directory entry."""
        iter_ = category_cb.get_active_iter()
        model = category_cb.get_model()

        if iter_ is None:
            category_cb.set_active_iter(model.iter_children(iter_))
            return True

        presentable = model.get_value(iter_, PoolModel.COLUMNS.PRESENTABLE)
        if presentable.TYPE == Presentable.TYPES.QUEUING:
            category_cb.set_active_iter(model.iter_children(iter_))
            return True
        else:
            self._active_category = presentable
            return False

