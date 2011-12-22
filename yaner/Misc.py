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
This module contains miscellaneous functions used by other modules.
"""

import sys
import urllib
import chardet
import argparse

from gi.repository.GObject import GObjectMeta
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import DeclarativeMeta, declared_attr

from yaner import __package__, __version__

class DeclarativeGObjectMeta(DeclarativeMeta, GObjectMeta):
    """Metaclass for Declarative and GObject subclasses."""
    pass

class SQLBase(object):
    """Base class for all SQLAlchemy classes."""

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)

class _VERSION(argparse.Action):
    """Show version information of the application."""

    def __call__(self, parser, namespace, values, option_string=None):
        print('{0} {1}'.format(__package__, __version__))
        print('Copyright (C) 2010-2011 Iven Hsu (Xu Lijian)')
        print(_('License GPLv3+: GNU GPL version 3 or later'))
        print('<http://gnu.org/licenses/gpl.html>.')
        print(_('This is free software:'))
        print(_('You are free to change and redistribute it.'))
        print(_('There is NO WARRANTY, to the extent permitted by law.'))
        sys.exit(0)

def unquote(string):
    """Unquote URI and auto detect encoding."""
    assert(isinstance(string, str))
    byte_string = urllib.parse.unquote_to_bytes(string)
    result = chardet.detect(byte_string)
    if result['confidence'] >= .8753:
        return byte_string.decode(result['encoding'])
    else:
        return string

