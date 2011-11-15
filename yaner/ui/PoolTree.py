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
import pango

from yaner.Presentable import Presentable
from yaner.ui.Misc import get_mix_color
from yaner.utils.Enum import Enum
from yaner.utils.Pretty import psize
from yaner.utils.Logging import LoggingMixin

class PoolModel(gtk.TreeStore, LoggingMixin):
    """
    The tree interface used by L{PoolView}.
    """

    COLUMNS = Enum(('PRESENTABLE', ))
    """
    The column names of the tree model, which is a L{Enum<yaner.utils.Enum>}.
    C{COLUMNS.NAME} will return the column number of C{NAME}.
    """

    def __init__(self):
        """L{PoolModel} initializing."""
        gtk.TreeStore.__init__(self, Presentable)
        LoggingMixin.__init__(self)

        self._pool_handlers = {}
        self._presentable_handlers = {}

    def add_pool(self, pool):
        """When a pool is added to the model, connect signals, and add all
        Presentables to the model.
        """
        self._pool_handlers[pool] = [
                pool.connect('presentable-added', self.on_presentable_added),
                pool.connect('presentable-removed', self.on_presentable_removed),
                ]
        for presentable in pool.presentables:
            self.add_presentable(presentable)

    def on_presentable_added(self, pool, presentable):
        """When new presentable appears in one of the pools, add it TODO
        the model.
        """
        self.add_presentable(presentable)

    def on_presentable_removed(self, pool, presentable):
        """
        When a presentable removed from one of the pools, remove it from
        the model.
        @TODO: Test this.
        """
        iter_ = self.get_iter_for_presentable(presentable)
        if iter_ is not None:
            self.remove(iter_)
        if presentable in self._presentable_handlers:
            presentable.disconnect(self._presentable_handlers.pop(presentable))

    def on_presentable_changed(self, presentable):
        """When a presentable changed, update the iter of the model."""
        iter_ = self.get_iter_for_presentable(presentable)
        if iter_:
            self.row_changed(self.get_path(iter_), iter_)

    def add_presentable(self, presentable):
        """Add a presentable to the model."""
        self.logger.debug(_('Adding presentable {0}...').format(
            presentable.name))
        parent = presentable.parent
        parent_iter = None
        if not parent is None:
            parent_iter = self.get_iter_for_presentable(parent)
            if parent_iter is None:
                self.logger.warning(_('No parent presentable for {0}.').format(
                    presentable.name))
                self.add_presentable(parent)
                parent_iter = self.get_iter_for_presentable(parent)
        iter_ = self.append(parent_iter)
        self.set(iter_, self.COLUMNS.PRESENTABLE, presentable)

        handler = presentable.connect('changed', self.on_presentable_changed)
        self._presentable_handlers[presentable] = handler

    def get_iter_for_presentable(self, presentable):
        """Get the TreeIter according to the presentable."""
        iter_ = self.get_iter_first()
        while not iter_ is None:
            if presentable is self.get_presentable(iter_):
                return iter_
            iter_ = self.iter_next(iter_)
        return None

    def get_presentable(self, iter_):
        """Get the presentable according to the given iter."""
        return self.get_value(iter_, self.COLUMNS.PRESENTABLE)

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

        # Set up TreeViewColumn
        column = gtk.TreeViewColumn()
        self.append_column(column)

        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, self._pixbuf_data_func)

        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._markup_data_func)

    @property
    def selection(self):
        """Get the C{gtk.TreeSelection} of the tree view."""
        return self.get_selection()

    @property
    def selected_presentable(self):
        """Get selected presentable."""
        (model, iter_) = self.selection.get_selected()
        return model.get_presentable(iter_)

    def _pixbuf_data_func(self, cell_layout, renderer, model, iter_):
        """Method for set the icon and its size in the column."""
        presentable = model.get_presentable(iter_)

        icons = ('gtk-connect',     # QUEUING
                'gtk-directory',    # CATEGORY
                'gtk-delete',       # DUSTBIN
                )
        icon = icons[presentable.TYPE]
        if presentable.TYPE == Presentable.TYPES.QUEUING and \
                not presentable.pool.connected:
            icon = 'gtk-disconnect'

        renderer.set_properties(
                stock_id = icon,
                stock_size = gtk.ICON_SIZE_LARGE_TOOLBAR,
                )

    def _markup_data_func(self, cell_layout, renderer, model, iter_):
        """
        Method for format the text in the column.
        """
        presentable = model.get_presentable(iter_)
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

        tasks = presentable.tasks
        total_length = sum(task.total_length for task in tasks)
        description = '{} Task(s) {}'.format(tasks.count(), psize(total_length))
        markup = '<small>' \
                     '<b>{}</b>\n' \
                     '<span fgcolor="{}">{}</span>' \
                 '</small>' \
                 .format(presentable.name, color, description)

        renderer.set_properties(
                markup = markup,
                ellipsize_set = True,
                ellipsize = pango.ELLIPSIZE_MIDDLE,
                )

