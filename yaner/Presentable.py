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
This module contains the L{Presentable} class of L{yaner}.
"""

import gobject

from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import reconstructor, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from yaner import SQLSession, SQLBase
from yaner.Task import Task
from yaner.utils.Enum import Enum
from yaner.utils.Logging import LoggingMixin

class Presentable(LoggingMixin, gobject.GObject):
    """
    The Presentable class of L{yaner}, which provides data for L{PoolModel}.
    """

    __gsignals__ = {
            'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            'task-added': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (Task,)),
            'task-removed': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Task,)),
            }
    """
    GObject signals of this class.
    """

    TYPES = Enum((
        'QUEUING',
        'CATEGORY',
        'DUSTBIN',
        ))
    """Presentable types."""

    def __init__(self):
        LoggingMixin.__init__(self)
        gobject.GObject.__init__(self)

    def add_task(self, task):
        """When task added, emit signals."""
        self.emit('changed')
        self.emit('task-added', task)

    def remove_task(self, task):
        """When task removed, emit signals."""
        self.emit('changed')
        self.emit('task-removed', task)

class Queuing(Presentable):
    """
    Queuing presentable of the L{Pool}s.
    """

    TYPE = Presentable.TYPES.QUEUING
    """Presentable type."""

    def __init__(self, pool):
        Presentable.__init__(self)
        self._pool = pool
        self.parent = None

    @property
    def name(self):
        """Get the name of the presentable."""
        return self.pool.name

    @name.setter
    def name(self, new_name):
        """Set the name of the presentable."""
        self.pool.name = new_name
        self.emit('changed')

    @property
    def pool(self):
        """Get the pool of the presentable."""
        return self._pool

    @property
    def tasks(self):
        """Get the running tasks of the pool."""
        return (task for task in self.pool.tasks if task.status not in \
                {Task.STATUSES.REMOVED, Task.STATUSES.COMPLETE})

class Category(SQLBase, Presentable):
    """
    Category presentable of the L{Pool}s.
    """

    TYPE = Presentable.TYPES.CATEGORY
    """Presentable type."""

    _name_ = Column(Unicode)
    directory = Column(Unicode)
    _tasks = relationship(Task, backref='category')
    pool_id = Column(Integer, ForeignKey('pool.id'))

    def __init__(self, name, directory, pool):
        self.name = name
        self.directory = directory
        self.pool = pool

        SQLSession.add(self)
        SQLSession.commit()

        self._init()

    @reconstructor
    def _init(self):
        Presentable.__init__(self)

        self.parent = self.pool.queuing

    def __repr__(self):
        return u"<Category {}>".format(self.name)

    @hybrid_property
    def name(self):
        return self._name_

    @name.setter
    def name(self, name):
        """When setting the name of the category, emit signal "changed"."""
        self._name_ = name
        if hash(self):
            self.emit('changed')

    @hybrid_property
    def tasks(self):
        return (task for task in self._tasks if task.status == Task.STATUSES.COMPLETE)

class Dustbin(Presentable):
    """
    Dustbin presentable of the L{Pool}s.
    """

    TYPE = Presentable.TYPES.DUSTBIN
    """Presentable type."""

    def __init__(self, pool):
        Presentable.__init__(self)
        self._pool = pool
        self.parent = pool.queuing

    @property
    def name(self):
        """Get the name of the presentable."""
        return _('Dustbin')

    @property
    def pool(self):
        """Get the pool of the presentable."""
        return self._pool

    @property
    def tasks(self):
        """Get the removed tasks of the pool."""
        return (task for task in self.pool.tasks \
                if task.status == Task.STATUSES.REMOVED)

