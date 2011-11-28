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
This module contains classes manipulating configuration files.
"""

import configparser

from yaner.XDG import load_first_config, save_config_file
from yaner.utils.Logging import LoggingMixin

class ConfigParser(LoggingMixin, configparser.ConfigParser):
    """This class provides a convenience way to access configuration files."""

    def __init__(self, filename):
        configparser.ConfigParser.__init__(self)
        LoggingMixin.__init__(self)

        # Read the config file
        self.read(load_first_config(filename))
        self.filename = filename

    def save(self):
        """Write changes to the file."""
        with open(save_config_file(self.filename), 'w') as config_file:
            self.write(config_file)

