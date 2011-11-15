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
This module contains the classes of the task list tree view on the
topright of the toplevel window.
"""

import gtk
import pango

from yaner.Task import Task
from yaner.ui.Misc import get_mix_color
from yaner.utils.Enum import Enum
from yaner.utils.Pretty import psize, pspeed
from yaner.utils.Logging import LoggingMixin

class TaskListModel(gtk.TreeStore, LoggingMixin):
    """
    The tree interface used by task list treeviews.
    """

    COLUMNS = Enum(('TASK', ))
    """
    The column names of the tree model, which is a L{Enum<yaner.utils.Enum>}.
    C{COLUMNS.NAME} will return the column number of C{NAME}.
    """

    def __init__(self, presentable = None):
        """
        L{TaskListModel} initializing.
        @arg tasks:Tasks providing data to L{TaskListModel}.
        @type tasks:L{yaner.Task}
        """
        gtk.TreeStore.__init__(self, Task)
        LoggingMixin.__init__(self)

        self._presentable = None

        self._presentable_handlers = {}
        self._task_handlers = {}

    @property
    def presentable(self):
        """Get the current presentable of the tree model."""
        return self._presentable

    @presentable.setter
    def presentable(self, new_presentable):
        """
        Set the current presentable of the tree model, and update it.
        """
        if self.presentable in self._presentable_handlers:
            for handler in self._presentable_handlers.pop(self.presentable):
                self.presentable.disconnect(handler)
        self._presentable_handlers[new_presentable] = [
                new_presentable.connect('task-added', self.on_task_added),
                new_presentable.connect('task-removed', self.on_task_removed),
                ]
        self._presentable = new_presentable

        self.clear()
        for task in new_presentable.tasks:
            self.add_task(task)

    def on_task_added(self, presentable, task):
        """
        When new task added in the presentable, add it to the model.
        """
        self.add_task(task)

    def on_task_removed(self, presentable, task):
        """
        When a task removed from the presentable, remove it from
        the model.
        @TODO: Test this.
        """
        iter_ = self.get_iter_for_task(task)
        if iter_ is not None:
            self.remove(iter_)
        if task in self._task_handlers:
            task.disconnect(self._task_handlers.pop(task))

    def on_task_changed(self, task):
        """
        When a task changed, update the iter of the model.
        """
        iter_ = self.get_iter_for_task(task)
        if iter_:
            self.row_changed(self.get_path(iter_), iter_)

    def add_task(self, task):
        """
        Add a task to the model.
        @TODO: Test this.
        """
        self.logger.debug(_('Adding task {}...').format(task.name))
        iter_ = self.insert(None, 0)
        self.set(iter_, self.COLUMNS.TASK, task)

        handler = task.connect('changed', self.on_task_changed)
        self._task_handlers[task] = handler

    def get_iter_for_task(self, task):
        """
        Get the TreeIter according to the task.
        @TODO: Test this.
        """
        iter_ = self.get_iter_first()
        while not iter_ is None:
            if task is self.get_value(iter_, self.COLUMNS.TASK):
                return iter_
            iter_ = self.iter_next(iter_)
        return None

class TaskListView(gtk.TreeView):
    """
    The C{gtk.TreeView} displaying L{TaskListModel}.
    """

    def __init__(self, model):
        """
        L{TaskListView} initializing.
        @arg model:The interface of the tree view.
        @type model:L{TaskListModel}
        """
        gtk.TreeView.__init__(self, model)

        # Set up columns
        column = gtk.TreeViewColumn(_('Task'))
        column.set_expand(True)
        column.set_resizable(True)
        self.append_column(column)

        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, self._status_data_func)

        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._desc_data_func)

        column = gtk.TreeViewColumn(_('Progress'))
        column.set_expand(True)
        column.set_resizable(True)
        self.append_column(column)

        renderer = gtk.CellRendererProgress()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._progress_data_func)

        column = gtk.TreeViewColumn(_('Speed'))
        column.set_expand(True)
        column.set_resizable(True)
        self.append_column(column)

        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._speed_data_func)

    @property
    def selection(self):
        """Get the C{gtk.TreeSelection} of the tree view."""
        return self.get_selection()

    def _status_data_func(self, cell_layout, renderer, model, iter_):
        """Method for set the icon and its size in the column."""
        task = model.get_value(iter_, model.COLUMNS.TASK)
        stock_ids = ('gtk-media-play',  # RUNNING
                'gtk-media-pause',      # PAUSED
                'gtk-apply',            # COMPLETED
                'gtk-stop',             # ERROR
                )
        renderer.set_properties(
                stock_id = stock_ids[task.status],
                stock_size = gtk.ICON_SIZE_LARGE_TOOLBAR,
                )

    def _desc_data_func(self, cell_layout, renderer, model, iter_):
        """Method for format the description text in the column."""
        task = model.get_value(iter_, model.COLUMNS.TASK)
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

        # If task completed, don't show completed length
        if task.status == Task.STATUSES.COMPLETED:
            completed_markup = ''
        else:
            completed_markup = '{} / '.format(psize(task.completed_length))

        markup = '<small>' \
                     '<b>{}</b>\n' \
                     '<span fgcolor="{}">{}{}</span>' \
                 '</small>' \
                 .format(task.name, color, completed_markup,
                         psize(task.total_length))

        renderer.set_properties(
                markup = markup,
                ellipsize_set = True,
                ellipsize = pango.ELLIPSIZE_END,
                )

    def _progress_data_func(self, cell_layout, renderer, model, iter_):
        """Method for set the progress bar style in the column."""
        task = model.get_value(iter_, model.COLUMNS.TASK)
        renderer.set_properties(
                value=task.percent * 100,
                text='{:.2%}'.format(task.percent),
                xpad = 2,
                ypad = 2,
                )

    def _speed_data_func(self, cell_layout, renderer, model, iter_):
        """Method for set the up and down speed in the column."""
        task = model.get_value(iter_, model.COLUMNS.TASK)
        markups = []
        if task.upload_speed:
            markups.append(u'\u2B06 {}'.format(pspeed(task.upload_speed)))
        if task.download_speed:
            markups.append(u'\n\u2B07 {}'.format(pspeed(task.download_speed)))
        renderer.set_properties(markup=''.join(markups))

