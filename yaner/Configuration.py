#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Yaner.

# Yaner - GTK+ interface for aria2 download mananger
# Copyright (C) 2010  Iven Day <ivenvd#gmail.com>
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
    This file contains classes manipulating configuration file
of Yaner, but could also be used by other programs.
"""

import ConfigParser
import os
from os.path import basename

from yaner.ODict import ODict

class ConfigFile(ODict):
    "Sections dict of config file handles add and del sections."

    instances = {}

    def __init__(self, config_file):
        if not os.path.exists(config_file):
            open(config_file, 'w').close()
        parser = ConfigParser.ConfigParser()
        parser.read(config_file)
        self.parser = parser
        section_list = [(section, ConfigSection(self, section)) \
                for section in parser.sections()]
        ODict.__init__(self, section_list)
        self.config_file = config_file

        # Add self to the global dict
        self.instances[basename(config_file)] = self

    def __str__(self):
        return self.config_file

    def __getattr__(self, attr):
        if self.has_key(attr):
            return self[attr]
        else:
            return ODict.__getattr__(self, attr)

    def __setitem__(self, section, option_dict):
        """
        To add a section, use "config_file[key] = {}".
        The dict contains all options in the section.
        """
        if not self.has_key(section):
            self.parser.add_section(section)
            ODict.__setitem__(self, section,
                    ConfigSection(self, section))
        for (key, value) in option_dict.iteritems():
            self[section][key] = value
        self.save()

    def __delitem__(self, section):
        """
        To delete a section, simply use "del config_file[key]".
        """
        self.parser.remove_section(section)
        ODict.__delitem__(self, section)
        self.save()

    def save(self):
        """
        Write changes to the disk.
        """
        with open(self.config_file, 'w') as cfile:
            self.parser.write(cfile)

class ConfigSection(ODict):
    "A section of config file with dict features."

    def __init__(self, config_file, section):
        ODict.__init__(self, config_file.parser.items(section))
        self.config_file = config_file
        self.parser = config_file.parser
        self.section = section

    def __str__(self):
        return dict.__str__(self)

    def __getattr__(self, key):
        return self[key]

    def __setitem__(self, key, value):
        self.parser.set(self.section, key, value)
        ODict.__setitem__(self, key, value)
        self.save()

    def __delitem__(self, key):
        self.parser.remove_option(self.section, key)
        ODict.__delitem__(self, key)
        self.save()

    def save(self):
        """
        Write changes to the disk.
        """
        self.config_file.save()

