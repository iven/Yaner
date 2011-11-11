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
This module contains the L{Task} class of L{yaner}.
"""

import gobject
import sqlobject

from yaner.Misc import GObjectSQLObjectMeta
from yaner.utils.Logging import LoggingMixin
from yaner.utils.Enum import Enum

class Task(sqlobject.SQLObject, gobject.GObject, LoggingMixin):
    """
    Task class is just downloading tasks, which provides data to L{TaskListModel}.
    """

    __metaclass__ = GObjectSQLObjectMeta

    __gsignals__ = {
            'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            'removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            }
    """
    GObject signals of this class.
    """

    TYPES = Enum((
        'NORMAL',
        'BT',
        'ML',
        ))
    """
    The types of the task, which is a L{Enum<yaner.utils.Enum>}.
    C{TYPES.NAME} will return the type number of C{NAME}.
    """

    STATUSES = Enum((
        'RUNNING',
        'PAUSED',
        'COMPLETED',
        'ERROR',
        ))
    """
    The statuses of the task, which is a L{Enum<yaner.utils.Enum>}.
    C{STATUSES.NAME} will return the type number of C{NAME}.
    """

    name = sqlobject.UnicodeCol()
    status = sqlobject.IntCol(default=STATUSES.PAUSED)
    deleted = sqlobject.BoolCol(default=False)
    type = sqlobject.IntCol()
    uris = sqlobject.PickleCol(default=[])
    percent = sqlobject.IntCol(default=0)
    size = sqlobject.IntCol(default=0)
    gid = sqlobject.StringCol(default='')
    metadata = sqlobject.PickleCol(default=None)
    options = sqlobject.PickleCol()

    pool = sqlobject.ForeignKey('Pool')
    category = sqlobject.ForeignKey('Category')

    def _init(self, *args, **kwargs):
        LoggingMixin.__init__(self)
        gobject.GObject.__init__(self)
        sqlobject.SQLObject._init(self, *args, **kwargs)
        self.progress_value = .96
        self.progress_text = '50MB/100MB'
        self.upload_speed = '20k/s'
        self.download_speed = '10k/s'
        self.connections = 2

