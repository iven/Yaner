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
This module contains the tree view classes of the C{gtk.TreeView} on the
left of the toplevel window.

A B{Pool} means a aria2 server, to avoid conflict with download servers.
"""

import gtk
import gobject
import pango
from gettext import gettext as _

from Misc import get_mix_color
from ..Presentable import Presentable
from ..utils.Logging import LoggingMixin
from ..utils.Enum import Enum

class PoolModel(gtk.TreeStore, LoggingMixin):
    """
    The tree interface used by L{PoolView}.
    """

    def __init__(self, pools):
        """
        L{PoolModel} initializing.
        @arg pools:Aria2 servers providing data to L{PoolModel}.
        @type pools:L{yaner.Pool}
        """
        gtk.TreeStore.__init__(self,
                gobject.TYPE_STRING,    # stock-id of the icon
                gobject.TYPE_STRING,    # name
                gobject.TYPE_STRING,    # description
                Presentable,            # presentable
                )
        LoggingMixin.__init__(self)

        self._columns = Enum((
            'ICON',
            'NAME',
            'DESCRIPTION',
            'PRESENTABLE',
            ))
        self.pools = pools

    @property
    def pools(self):
        """Get the pools of the tree model."""
        return self._pools

    @pools.setter
    def pools(self, new_pools):
        """
        Set the pools of the tree model, and update it.
        """
        self.clear()
        for pool in new_pools:
            pool.connect('presentable-added', self.on_presentable_added)
            pool.connect('presentable-removed', self.on_presentable_removed)
            pool.connect('presentable-changed', self.on_presentable_changed)
            for presentable in pool.presentables:
                self.add_presentable(presentable)
        self._pools = new_pools

    @property
    def columns(self):
        """
        Get the column names of the tree model, which is a
        L{Enum<yaner.utils.Enum>}. C{columns.NAME} will return the column
        number of C{NAME}.
        """
        return self._columns

    def on_presentable_added(self, pool, presentable):
        """
        When new presentable appears in one of the pools, add it to the model.
        @TODO: Test this.
        """
        self.add_presentable(presentable)

    def on_presentable_removed(self, pool, presentable):
        """
        When a presentable removed from one of the pools, remove it from
        the model.
        @TODO: Test this.
        """
        iter_ = self.get_iter_for_presentable(presentable)
        if iter_ != None:
            self.remove(_iter)

    def on_presentable_changed(self, pool, presentable):
        """
        When a presentable changed, update the iter of the model.
        @TODO: Test this.
        """
        if presentable in pool.presentables:
            iter_ = self.get_iter_for_presentable(presentable)
            self.set_data_for_presentable(iter_, presentable)

    def add_presentable(self, presentable):
        """
        Add a presentable to the model.
        @TODO: Test this.
        """
        self.logger.debug(_('Adding presentable {}...').format(presentable.uuid))
        parent = presentable.parent
        parent_iter = None
        if not parent is None:
            parent_iter = self.get_iter_for_presentable(parent)
            if parent_iter is None:
                self.logger.warning(_('No parent for {}.').format(presentable.uuid))
                self.add_presentable(parent)
                parent_iter = self.get_iter_for_presentable(parent)
        iter_ = self.append(parent_iter)
        self.set_data_for_presentable(iter_, presentable)

    def set_data_for_presentable(self, iter_, presentable):
        """
        Update the iter data for presentable.
        @TODO: Test this.
        """
        self.set(iter_,
                self.columns.ICON, presentable.icon,
                self.columns.DESCRIPTION, presentable.description,
                self.columns.NAME, presentable.name,
                self.columns.PRESENTABLE, presentable,
                )

    def get_iter_for_presentable(self, presentable):
        """
        Get the TreeIter according to the presentable.
        @TODO: Test this.
        """
        iter_ = self.get_iter_first()
        while not iter_ is None:
            if presentable is self.get_value(iter_, self.columns.PRESENTABLE):
                return iter_
            iter_ = self.iter_next(iter_)
        return None

class PoolView(gtk.TreeView):
    """
    The C{gtk.TreeView} displaying L{PoolModel}.
    """

    def __init__(self, model):
        """
        L{PoolView} initializing.
        @arg model:The interface of the tree view.
        @type model:L{PoolModel}
        """
        gtk.TreeView.__init__(self, model)

        self._model = model

        # Set up TreeViewColumn
        column = gtk.TreeViewColumn()
        self.append_column(column)

        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, self._pixbuf_data_func)

        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._markup_data_func)

        # TreeView properties
        self.set_headers_visible(False)
        self.set_show_expanders(False)
        self.set_level_indentation(16)
        self.expand_all()

        self.selection.set_mode(gtk.SELECTION_SINGLE)

    @property
    def model(self):
        """Get the L{model<PoolModel>} of the tree view."""
        return self._model

    @property
    def selection(self):
        """Get the C{gtk.TreeSelection} of the tree view."""
        return self.get_selection()

    def _pixbuf_data_func(self, cell_layout, renderer, model, iter_):
        """Method for set the icon and its size in the column."""
        stock_id = model.get_value(iter_, self.model.columns.ICON)
        renderer.set_properties(
                stock_id = stock_id,
                stock_size = gtk.ICON_SIZE_LARGE_TOOLBAR,
                )

    def _markup_data_func(self, cell_layout, renderer, model, iter_):
        """
        Method for format the text in the column.
        """
        (name, description) = model.get(
                iter_,
                self.model.columns.NAME,
                self.model.columns.DESCRIPTION,
                )
        # Get current state of the iter
        if self.selection.iter_is_selected(iter_):
            if self.has_focus():
                state = gtk.STATE_SELECTED
            else:
                state = gtk.STATE_ACTIVE
        else:
            state = gtk.STATE_NORMAL
        # Get the color for the description
        color = get_mix_color(self, state)

        markup = '<small>' \
                     '<b>{name}</b>\n' \
                     '<span fgcolor="{color}">{description}</span>' \
                 '</small>' \
                 .format(**locals())

        renderer.set_properties(
                markup = markup,
                ellipsize_set = True,
                ellipsize = pango.ELLIPSIZE_MIDDLE,
                )

