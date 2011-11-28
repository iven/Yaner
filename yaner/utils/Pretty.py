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

"""This module contains functions converting bytes to human readable format."""

_SUFFIXES = ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')

def psize(size):
    """This function converts byte sizes to pretty format."""
    for (i, suffix) in enumerate(_SUFFIXES):
        if size < 1024:
            break
        size /= 1024.0
    return '{:.2f} {}'.format(size, suffix)

def pspeed(speed):
    """This is the speed version of L{psize}."""
    return '{}/s'.format(psize(speed))

