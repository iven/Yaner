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
This module contains the L{Dustbin} presentable of L{yaner}.
"""

from yaner.Presentable import Presentable
from yaner.Configurations import DUSTBIN_CONFIG

class Dustbin(Presentable):
    """
    Dustbin presentable of the L{Pool}s.
    """
    def __init__(self, uuid_, queuing):
        Presentable.__init__(self, uuid_, DUSTBIN_CONFIG)
        self.parent = queuing
        self.icon = "gtk-delete"

    @property
    def name(self):
        """Get the name of the presentable."""
        return _('Dustbin')

    @property
    def description(self):
        """Get the description of the presentable."""
        return "This is a dustbin."

