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
This module contains the super class of applications that need loggers.
"""

import logging

class LoggingMixin(object):
    """
    This class provides the L{logger} property to its subclasses.
    """

    def __init__(self):
        """Get the logger and set it as property. """
        self._name = "{0}.{1}".format(self.__module__, self.__class__.__name__)
        self._logger = None

    @property
    def logger(self):
        """Get the logger of this module."""
        if self._logger is None:
            self._logger = logging.getLogger(self._name)
        return self._logger

