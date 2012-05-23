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
This module contains the emunerate class like in C / C++.
"""

class Enum(object):
    """
    The emunerate class like in C / C++. Usage:

    >>> from Enum import Enum
    >>> msgtype = Enum('a', 'b', 'c')
    >>> msgtype.a
    0
    >>> msgtype.b
    1
    >>> msgtype[0]
    'a'
    """
    def __init__(self, *names):
        """
        Extract attributes from L{names}.
        @arg names:Enum names. Each name is a C{str}.
        @type names:C{tuple} or C{list}
        """
        for num, name in enumerate(names):
            setattr(self, name, num)

