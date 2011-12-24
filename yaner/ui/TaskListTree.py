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
This module contains the classes of the task list tree view on the
topright of the toplevel window.
"""

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Pango

from yaner.Task import Task
from yaner.ui.Misc import get_mix_color
from yaner.utils.Enum import Enum
from yaner.utils.Pretty import psize, pspeed
from yaner.utils.Logging import LoggingMixin

class TaskListModel(Gtk.TreeStore, LoggingMixin):
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
        Gtk.TreeStore.__init__(self, Task)
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
        """Set the current presentable of the tree model, and update it."""
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
        """When new task added in the presentable, add it to the model."""
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
        """When a task changed, update the iter of the model."""
        iter_ = self.get_iter_for_task(task)
        if iter_:
            self.row_changed(self.get_path(iter_), iter_)

    def add_task(self, task):
        """Add a task to the model."""
        if not self.get_iter_for_task(task):
            self.logger.debug(_('Adding {}...').format(task))
            iter_ = self.insert(None, 0)
            self.set(iter_, self.COLUMNS.TASK, task)

            handler = task.connect('changed', self.on_task_changed)
            self._task_handlers[task] = handler

    def get_iter_for_task(self, task, parent=None):
        """Get the TreeIter according to the task."""
        iter_ = self.iter_children(parent)
        while not iter_ is None:
            if task is self.get_task(iter_):
                return iter_

            result = self.get_iter_for_task(task, iter_)
            if result:
                return result

            iter_ = self.iter_next(iter_)
        return None

    def get_task(self, iter_):
        """Get the task according to the given iter."""
        return self.get_value(iter_, self.COLUMNS.TASK)

class TaskListView(Gtk.TreeView):
    """
    The C{Gtk.TreeView} displaying L{TaskListModel}.
    """

    def __init__(self, model):
        """
        L{TaskListView} initializing.
        @arg model:The interface of the tree view.
        @type model:L{TaskListModel}
        """
        Gtk.TreeView.__init__(self, model)

        # Set up columns
        column = Gtk.TreeViewColumn(_('Tasks'))
        column.set_expand(True)
        column.set_resizable(True)
        self.append_column(column)

        renderer = Gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, self._status_data_func)

        renderer = Gtk.CellRendererText()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._desc_data_func)

        column = Gtk.TreeViewColumn(_('Progress'))
        column.set_expand(True)
        column.set_resizable(True)
        self.append_column(column)

        renderer = Gtk.CellRendererProgress()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._progress_data_func)

        column = Gtk.TreeViewColumn(_('Speed'))
        column.set_resizable(True)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._speed_data_func)

        column = Gtk.TreeViewColumn(_('Connections'))
        column.set_resizable(True)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column.pack_start(renderer, True)
        column.set_cell_data_func(renderer, self._connection_data_func)

    @property
    def selection(self):
        """Get the C{Gtk.TreeSelection} of the tree view."""
        return self.get_selection()

    @property
    def selected_tasks(self):
        """Get selected tasks."""
        (model, paths) = self.selection.get_selected_rows()
        return [model.get_task(model.get_iter(path)) for path in paths]

    def _status_data_func(self, column, renderer, model, iter_, data=None):
        """Method for set the icon and its size in the column."""
        task = model.get_task(iter_)
        statuses = Task.STATUSES
        stock_ids = {statuses.ACTIVE: 'gtk-media-play',
                statuses.WAITING: 'gtk-refresh',
                statuses.PAUSED: 'gtk-media-pause',
                statuses.COMPLETE: 'gtk-apply',
                statuses.ERROR: 'gtk-stop',
                statuses.TRASHED: 'gtk-delete',
                statuses.INACTIVE: 'gtk-disconnect',
                }
        renderer.set_properties(
                stock_id = stock_ids[task.status],
                stock_size = Gtk.IconSize.LARGE_TOOLBAR,
                )

    def _desc_data_func(self, column, renderer, model, iter_, data=None):
        """Method for format the description text in the column."""
        task = model.get_task(iter_)
        # Get current state of the iter
        if self.selection.iter_is_selected(iter_):
            if self.has_focus():
                state = Gtk.StateType.SELECTED
            else:
                state = Gtk.StateType.ACTIVE
        else:
            state = Gtk.StateType.NORMAL
        # Get the color for the description
        color = get_mix_color(self, state)

        # If task completed, don't show completed length
        if task.status == Task.STATUSES.COMPLETE:
            completed_text = ''
        else:
            completed_text = '{} / '.format(psize(task.completed_length))

        markup = '<small>' \
                     '<b>{}</b>\n' \
                     '<span fgcolor="{}">{}{}</span>' \
                 '</small>' \
                 .format(GLib.markup_escape_text(task.name),
                         color, completed_text, psize(task.total_length))

        renderer.set_properties(
                markup = markup,
                ellipsize_set = True,
                ellipsize = Pango.EllipsizeMode.END,
                )

    def _progress_data_func(self, column, renderer, model, iter_, data=None):
        """Method for set the progress bar style in the column."""
        task = model.get_task(iter_)
        percent = 0 if (task.total_length == 0) else \
                (task.completed_length / task.total_length)

        renderer.set_properties(
                value=percent * 100,
                text='{:.2%}'.format(percent),
                xpad = 2,
                ypad = 2,
                )

    def _speed_data_func(self, column, renderer, model, iter_, data=None):
        """Method for set the up and down speed in the column."""
        task = model.get_task(iter_)
        text = []
        if task.status == Task.STATUSES.ACTIVE:
            if task.upload_speed:
                text.append('\u2B06 {}'.format(pspeed(task.upload_speed)))
            if task.download_speed:
                text.append('\u2B07 {}'.format(pspeed(task.download_speed)))
        renderer.set_properties(text='\n'.join(text))

    def _connection_data_func(self, column, renderer, model, iter_, data=None):
        """Method for set the connections in the column."""
        task = model.get_task(iter_)
        if task.status == Task.STATUSES.ACTIVE:
            text = task.connections
        else:
            text = ''
        renderer.set_properties(text=text, xalign=.5, yalign=.5)

