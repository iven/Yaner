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
import gobject
import pango

from yaner.Task import Task
from yaner.Presentable import Presentable
from yaner.ui.Misc import get_mix_color
from yaner.utils.Logging import LoggingMixin
from yaner.utils.Enum import Enum

class TaskListModel(gtk.TreeStore, LoggingMixin):
    """
    The tree interface used by task list treeviews.
    """

    def __init__(self, presentable):
        """
        L{TaskListModel} initializing.
        @arg tasks:Tasks providing data to L{TaskListModel}.
        @type tasks:L{yaner.Task}
        """
        gtk.TreeStore.__init__(self,
                gobject.TYPE_STRING,    # gid
                gobject.TYPE_STRING,    # status
                gobject.TYPE_STRING,    # name
                gobject.TYPE_FLOAT,     # progress value
                gobject.TYPE_STRING,    # progress text
                gobject.TYPE_STRING,    # size
                gobject.TYPE_STRING,    # download speed
                gobject.TYPE_STRING,    # upload speed
                gobject.TYPE_INT,       # connections
                gobject.TYPE_STRING,    # uuid
                Task,                   # task
                )
        LoggingMixin.__init__(self)

        self._columns = Enum((
            'GID',
            'STATUS',
            'NAME',
            'PRGRESS_VALUE',
            'PRGRESS_TEXT',
            'SIZE',
            'DOWNLOAD_SPEED',
            'UPLOAD_SPEED',
            'CONNECTIONS',
            'UUID',
            'TASK',
            ))
        self._presentable = presentable

    @property
    def presentable(self):
        """Get the presentable of the tree model."""
        return self._presentable

    @presentable.setter
    def presentable(self, new_presentable):
        """
        Set the presentable of the tree model, and update it.
        """
        self.clear()
        presentable.connect('task-added', self.on_task_added)
        presentable.connect('task-removed', self.on_task_removed)
        presentable.connect('task-changed', self.on_task_changed)
        for task in presentable.tasks:
            self.add_task(task)
        self._presentable = new_presentable

    @property
    def columns(self):
        """
        Get the column names of the tree model, which is a
        L{Enum<yaner.utils.Enum>}. C{columns.NAME} will return the column
        number of C{NAME}.
        """
        return self._columns

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
        if iter_ != None:
            self.remove(_iter)

    def on_task_changed(self, presentable, task):
        """
        When a task changed, update the iter of the model.
        @TODO: Test this.
        """
        if task in presentable.tasks:
            iter_ = self.get_iter_for_task(task)
            self.set_data_for_task(iter_, task)

    def add_task(self, task):
        """
        Add a task to the model.
        @TODO: Test this.
        """
        self.logger.debug(_('Adding task {}...').format(
            task.uuid))
        iter_ = self.append()
        self.set_data_for_task(iter_, task)

    def set_data_for_task(self, iter_, task):
        """
        Update the iter data for task.
        """
        self.set(iter_,
                self.columns.GID, task.gid,
                self.columns.STATUS, task.status,
                self.columns.NAME, task.name,
                self.columns.PRGRESS_VALUE, task.progress_value,
                self.columns.PRGRESS_VALUE, task.progress_text,
                self.columns.SIZE, task.size,
                self.columns.DOWNLOAD_SPEED, task.download_speed,
                self.columns.UPLOAD_SPEED, task.upload_speed,
                self.columns.CONNECTIONS, task.connections,
                self.columns.UUID, task.uuid,
                self.columns.TASK, task,
                )

    def get_iter_for_task(self, task):
        """
        Get the TreeIter according to the task.
        @TODO: Test this.
        """
        iter_ = self.get_iter_first()
        while not iter_ is None:
            if task is self.get_value(iter_, self.columns.TASK):
                return iter_
            iter_ = self.iter_next(iter_)
        return None

