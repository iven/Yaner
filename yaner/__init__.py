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
This module contains classes and constants of Yaner download manager.
Currently it could not be used by other programs.

Package Organization
====================
The L{yaner} package contains the following subpackages and modules:

G{packagetree}

@author:U{Iven<mailto:ivenvd@gmail.com>}
@organization:U{USTC<http://www.ustc.edu.cn/>}
@copyright:S{copy} 2010-2011 Iven
@license:GPLv3
@see:U{The Yaner webpage<https://github.com/iven/Yaner>}, U{The
author's blog<http://www.kissuki.com/>}(In Chinese)
@requires:
"""

__package__ = "yaner"
"""
The module level attribute.
@see:U{PEP-366<http://www.python.org/dev/peps/pep-0366/>}.
"""

__version__ = '0.4.0'
"""
The version of L{yaner}.
This is also used by the setup script.
"""

__author__    = "Iven Hsu (Xu Lijian) <ivenvd@gmail.com>"
"""The primary author of L{yaner}."""

__license__   = "GPLv3"
"""The license governing the use and distribution of L{yaner}."""

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from yaner.Misc import SQLBase, DeclarativeGObjectMeta

SQLSession = scoped_session(sessionmaker())
SQLBase = declarative_base(cls=SQLBase, metaclass=DeclarativeGObjectMeta)

