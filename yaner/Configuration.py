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

import ConfigParser

class ConfigFile(dict):
    "Sections dict of config file handles add and del sections."

    def __init__(self, config_file):
        cp = ConfigParser.ConfigParser()
        cp.read(config_file)
        section_dict = dict((section, ConfigSection(cp, section)) \
                for section in cp.sections())
        dict.__init__(self, section_dict)
        self.cp = cp
        self.config_file = config_file

    def __getattr__(self, key):
        return self[key]

    def __setitem__(self, section, option_dict):
        """
        To add a section, use "config_file[key] = {}".
        The dict contains all options in the section.
        """
        if not self.has_key(section):
            self.cp.add_section(section)
            dict.__setitem__(self, section,
                    ConfigSection(self.cp, section))
        for (key, value) in option_dict.items():
            self[section][key] = value

    def __delitem__(self, section):
        """
        To delete a section, simply use "del config_file[key]".
        """
        self.cp.remove_section(section)
        dict.__delitem__(self, section)

    def __del__(self):
        with open(self.config_file, 'w') as f:
            self.cp.write(f)

class ConfigSection(dict):
    "A section of config file with dict features."

    def __init__(self, config_parser, section):
        dict.__init__(self, config_parser.items(section))
        self.cp = config_parser
        self.section = section

    def __getattr__(self, key):
        return self[key]

    def __setitem__(self, key, value):
        self.cp.set(self.section, key, value)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        self.cp.remove_option(self.section, option)
        dict.__delitem__(self, key)

