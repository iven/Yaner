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

from Logging import LoggingMixin

class ConfigParser(LoggingMixin, SafeConfigParser):
    """A configuration file parser."""

    def __init__(self, dir_in, file_in = None, sections = (),
            dir_out = None, file_out = None):
        """
        The method create a L{_ConfigSection} for each section in the
        configuration file.

        Usage:
            1. Create a new file I{/dir/B{UUID}} with sections:

            >>> ConfigParser('/dir', sections = ('section1', 'section2'))

            2. Read existing file I{/dir/file}:

            >>> ConfigParser('/dir', 'file')

            3. Create a new file I{/dir1/B{UUID}} based on existing file
            I{/dir/file}:

            >>> ConfigParser('/dir', 'file', dir_out = '/dir1')

            4. Create a new file I{/d1/f1} based on existing file I{/dir/file}:

            >>> ConfigParser('/dir', 'file', dir_out = '/d1', file_out = 'f1')

        @arg dir_in:The base directory of the input file.
        @arg file_in:The filename of the input file.
        @arg sections:The sections of the file, which should not be added nor
        deleted after creation.
        @arg dir_out:The base directory of the output file.
        @arg file_out:The filename of the output file.

        @type dir_in:C{str}
        @type file_in:C{str}
        @type sections:C{tuple} or C{list}
        @type dir_out:C{str}
        @type file_out:C{str}
        """

        SafeConfigParser.__init__(self)
        LoggingMixin.__init__(self)

        # Initialize file path
        if file_out is None:
            self._file_out = str(uuid.uuid4())
            if file_in is None:
                file_in = self._file_out
        else:
            self._file_out = file_out

        if dir_out is None:
            self._dir_out = dir_in
        else:
            self._dir_out = dir_out

        if not os.path.exists(self._dir_out):
            os.makedirs(self._dir_out)
            self.logger.info("Created directory {}.".format(self._dir_out))

        # Read the config file
        self.read(os.path.join(dir_in, file_in))
        self.save()

        # Initialize sections
        if not self.sections():
            # This is a new file
            for section in sections:
                self.add_section(section)
            self.save()
        self._sections_ = {}
        for section in self.sections():
            # Create ConfigSection for each section
            self._sections_[section] = _ConfigSection(self, section)

    @property
    def file(self):
        """Get the filename of the output file."""
        return self._file_out

    @property
    def dir(self):
        """Get the directory of the output file."""
        return self._dir_out

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
        Set the contents of C{section}. The original contents will be removed.
        Usage:
            >>> config['section'] = {'option1': 'value1', 'option2': 'value2'}

        @arg option_dict:Key is the option, value is the value of the option.
        @arg option_dict:C{dict}
        """
        self.remove_section(section)
        self.add_section(section)

        for (key, value) in option_dict.iteritems():
            self[section][key] = value
        self.save()

    def save(self):
        """Write changes to the file."""
        with open(os.path.join(self.dir_, self.file_), 'w') as config_file:
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

