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

A B{Pool} means a aria2 server, to avoid conflect with download servers.
"""

import gtk
import gobject

class PoolModel(gtk.TreeStore):
    """
    The tree interface used by L{PoolView}.
    """

    def __init__(self, pools):
        """
        L{PoolModel} initializing.
        @arg pools:Aria2 servers providing data to L{PoolModel}.
        @type pools:yaner.Pool
        @TODO:Update the type of L{pools}.
        """
        gtk.TreeStore.__init__(self,
                gobject.TYPE_STRING,    # stock-id
                gobject.TYPE_STRING,    # name
                gobject.TYPE_STRING,    # description
                )

        self._pools = pools

    @property
    def pools(self):
        """Get the pools of the tree model."""
        return self._pools

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
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)

        # TreeView properties
        self.set_headers_visible(False)
        self.set_show_expanders(False)
        self.set_level_indentation(16)
        self.expand_all()

    @property
    def model(self):
        """Get the L{model<PoolModel>} of the tree view."""
        return self._model

