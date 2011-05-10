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
This module contains the L{Task} class of L{yaner}.
"""

import os
import gobject

from yaner.utils.Logging import LoggingMixin
from yaner.Constants import U_CONFIG_DIR
from yaner.utils.Configuration import ConfigParser
from yaner.utils.Enum import Enum

class Task(LoggingMixin, gobject.GObject):
    """
    Task class is just downloading tasks, which provides data to L{TaskListModel}.
    """

    __gsignals__ = {
            'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            'removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            }
    """
    GObject signals of this class.
    """

    _CONFIG_DIR = os.path.join(U_CONFIG_DIR, 'tasks')
    """
    User config directory containing task configuration files.
    """

    TYPES = Enum((
        'NORMAL',
        'BT',
        'ML',
        ))
    """
    The types of the task, which is a L{Enum<yaner.utils.Enum>}.
    C{TASKS.NAME} will return the type number of C{NAME}.
    """

    def __init__(self, uuid_, config):
        LoggingMixin.__init__(self)
        gobject.GObject.__init__(self)

        self._uuid = uuid_
        self._config = None

    @property
    def uuid(self):
        """Get the uuid of the task."""
        return self._uuid

    @property
    def config(self):
        """
        Get the configuration of the task.
        If the file doesn't exist, read from the default configuration.
        If the task configuration directory doesn't exist, create it.
        """
        if self._config is None:
            config = ConfigParser(self._CONFIG_DIR, self.uuid)
            if config.empty():
                self.logger.info(
                        _('No task configuration file, creating...'))
                config.update(default_config)
                self._uuid = config.file
            self._config = config
        return self._config

