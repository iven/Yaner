#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Yaner.

# Yaner - GTK+ interface for aria2 download mananger
# Copyright (C) 2010  Iven Day <ivenvd#gmail.com>
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
    This file contains functions converting numbers
    to human readable format.
"""

from __future__ import division

def psize(num):
    """
    This function converts byte sizes into pretty format.
    i.e., 1024 -> 1 KB.
    """
    num = int(num)
    units = ('B', 'KB', 'MB', 'GB', 'TB')
    for i in xrange(len(units)):
        if num < 1024 ** (i + 1) * 2 or i == len(units) - 1:
            num = '%.1f %s' % (num / (1024 ** i), units[i])
            break
    return num

def pspeed(num):
    """
    This is the speed version of psize.
    """
    return psize(num) + '/s'
