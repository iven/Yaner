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
This module contains the L{Category} presentable of L{yaner}.
"""

import sqlobject

from yaner.Presentable import Presentable

class Category(Presentable, sqlobject.SQLObject):
    """
    Category presentable of the L{Pool}s.
    """

    name = sqlobject.UnicodeCol()
    directory = sqlobject.UnicodeCol()

    pool = sqlobject.ForeignKey('Pool')
    tasks = sqlobject.MultipleJoin('Task')

    def _init(self, *args, **kwargs):
        Presentable.__init__(self)
        sqlobject.SQLObject._init(self, *args, **kwargs)

        self.parent = kwargs['queuing']
        self.icon = "gtk-directory"

    @property
    def description(self):
        """Get the description of the presentable."""
        return "This is a category."

