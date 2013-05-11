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
This module contains classes and constants related to database.
"""

from PyQt4.QtCore import pyqtWrapperType
from sqlalchemy import Column, Integer
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta, declared_attr

class DeclarativeGObjectMeta(pyqtWrapperType, DeclarativeMeta):
    """Metaclass for Declarative and QObject subclasses."""
    pass

class _SQLBase(object):
    """Base class for all SQLAlchemy classes."""

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)

SQLSession = scoped_session(sessionmaker())
SQLBase = declarative_base(cls=_SQLBase, metaclass=DeclarativeGObjectMeta)

