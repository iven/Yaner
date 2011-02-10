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
This module contains the L{Pool} class of L{yaner}.
"""

class Pool(object):
    """
    The Pool class of L{yaner}, which provides data for L{PoolModel}.

    A Pool is just a aria2 server, to avoid conflict with download server.
    """
    def __init__(self, uuid_ = None):
        self._uuid_ = uuid_

    @property
    def uuid(self):
        """Get the uuid of the pool."""
        return self._uuid_

    @property
    def config(self):
        """Get the configuration of the pool."""
        return self._config

    def _init_config(self):
        """
        Open pool configuration file as L{self.config}.
        If the file doesn't exist, read from the default configuration.
        If the pool configuration directory doesn't exist, create it.
        """
        if self.uuid is None:
            self._config = ConfigParser(
                    dir_in   = CONFIG_DIR,
                    file_in  = self._CONFIG_FILE,
                    dir_out  = self._CONFIG_DIR,
                    file_out = self._CONFIG_FILE
                    )
            self.uuid = self._config.file
        else:
            self._config = ConfigParser(
                    dir_in  = self._CONFIG_DIR,
                    file_in = self._CONFIG_FILE
                    )

