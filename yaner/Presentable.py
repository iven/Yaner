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

from yaner.Task import Task
from yaner.utils.Logging import LoggingMixin

class Presentable(LoggingMixin, gobject.GObject):
    """
    The Presentable class of L{yaner}, which provides data for L{PoolModel}.
    """

    __gsignals__ = {
            'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            'removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            'task-added': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (Task,)),
            'task-removed': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Task,)),
            'task-changed': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Task,)),
            }
    """
    GObject signals of this class.
    """

    def _init(self, *args, **kwargs):
        LoggingMixin.__init__(self)
        gobject.GObject.__init__(self)

