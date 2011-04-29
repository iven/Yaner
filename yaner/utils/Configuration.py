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
This module contains classes manipulating configuration files.
"""

import os
import uuid
from ConfigParser import SafeConfigParser

from yaner.utils.Logging import LoggingMixin

class ConfigParser(LoggingMixin, SafeConfigParser):
    """A configuration file parser."""

    def __init__(self, dir_, file_ = None):
        """
        The method create a L{_ConfigSection} for each section in the
        configuration file.

        Usage:
            1. Read existing file I{/dir/file}:

            >>> ConfigParser('/dir', 'file')

            2. Create a new file I{/dir1/B{UUID}}:

            >>> ConfigParser('/dir')

        @arg dir_:The base directory of the file.
        @type dir_:C{str}
        @arg file_:The filename of the file.
        @type file_:C{str} or C{None}
        """

        SafeConfigParser.__init__(self)
        LoggingMixin.__init__(self)

        # Initialize file path
        if not os.path.exists(dir_):
            os.makedirs(dir_)
            self.logger.info(_("Created directory {0}.").format(dir_))
        self._dir = dir_
        self._file = str(uuid.uuid4()) if file_ in ('', None) else file_

        # Read the config file
        self.read(os.path.join(self._dir, self._file))

        # Initialize sections
        self._sections_ = {}
        for section in self.sections():
            # Create ConfigSection for each section
            self._sections_[section] = _ConfigSection(self, section)

    @property
    def file(self):
        """Get the filename of the file."""
        return self._file

    @property
    def dir(self):
        """Get the directory of the file."""
        return self._dir

    @property
    def sections_(self):
        """
        Get the section dict, the key of which is section name, and the value
        is of type L{_ConfigSection}.
        """
        return self._sections_

    def __getitem__(self, section):
        """
        Get the L{_ConfigSection} of C{section}. Usage:
            >>> value1 = config['section']['option1']
        """
        return self.sections_[section]

    def __setitem__(self, section, option_dict):
        """
        Set the content of C{section}. The original content will be removed.
        Usage:
            >>> config['section'] = {'option1': 'value1', 'option2': 'value2'}

        @arg option_dict:Key is the option, value is the value of the option.
        @arg option_dict:C{dict}
        """
        if section in self.sections():
            self.remove_section(section)
            del self._sections_[section]

        self.add_section(section)
        self._sections_[section] = _ConfigSection(self, section)

        for (option, value) in option_dict.iteritems():
            self[section][option] = value
        self.save()

    def empty(self):
        """
        Check if the configuration file is empty.
        """
        return not bool(self.sections())

    def update(self, content):
        """
        Update the configuration file with the C{content} provided.
        @arg content:The sections and options of the file.
        @type content:C{dict}
        """
        for (section, options) in content.items():
            self[section] = options

    def save(self):
        """Write changes to the file."""
        with open(os.path.join(self.dir, self.file), 'w') as config_file:
            self.write(config_file)

class _ConfigSection(object):
    "A section of a configuration file."

    def __init__(self, parser, name):
        self._parser = parser
        self._name = name

    @property
    def parser(self):
        """Get the config parser."""
        return self._parser

    @property
    def name(self):
        """Get the section name."""
        return self._name

    def __getitem__(self, option):
        """
        Get the value of the C{option} in this section. Usage:
            >>> value1 = config['section']['option1']
        """
        return self.parser.get(self.name, option)

    def __setitem__(self, option, value):
        """
        Set the C{value} of the C{option} in this section. Usage:
            >>> config['section']['option1'] = value1
        """
        self.parser.set(self.name, option, str(value))
        self.parser.save()

    def __delitem__(self, option):
        """
        Delete an C{option} in this section. Usage:
            >>> del config['section']['option1']
        """
        self.parser.remove_option(self.name, option)
        self.parser.save()

