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

import os
import gobject
from gettext import gettext as _

from Constants import U_CONFIG_DIR
from utils.Logging import LoggingMixin
from utils.Configuration import ConfigParser

class Pool(LoggingMixin, gobject.GObject):
    """
    The Pool class of L{yaner}, which provides data for L{PoolModel}.

    A Pool is just a connection to the aria2 server, to avoid name conflict
    with download server.
    """

    __gsignals__ = {
            'disconnected': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ()),
            'presentable-added': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Presentable)),
            'presentable-removed': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Presentable)),
            'presentable-changed': (gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (Presentable)),
            }
    """
    GObject signals of this class.
    """

    _CONFIG_DIR = os.path.join(U_CONFIG_DIR, 'pool')
    """
    User config directory containing pool configuration files.
    """

    def __init__(self, uuid_ = None):
        LoggingMixin.__init__(self)
        gobject.GObject.__init__(self)

        self._uuid_ = uuid_
        self._config = self._init_config()

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
        config = ConfigParser(self._CONFIG_DIR, self.uuid)
        if config.empty():
            self.logger.info(_('No pool configuration file, creating...'))
            from Configurations import POOL_CONFIG
            config.update(POOL_CONFIG)
        return config

