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
This module contains the L{Queuing} presentable of L{yaner}.
"""

from Presentable import Presentable
from Configurations import QUEUING_CONFIG

class Queuing(Presentable):
    """
    Queuing presentable of the L{Pool}s.
    """
    def __init__(self, pool, uuid_):
        Presentable.__init__(self, uuid_, QUEUING_CONFIG)
        self.parent = None
        self.name = "My Computer"
        self.description = "This is a test."
        self.icon = "gtk-apply"

