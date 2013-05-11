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

"""This module contains and functions to load and save from and to XDG directories.
Functions in this module automatically add __module__ prefix to the paths.
"""

import os
import subprocess

from functools import partial

from yaner import __package__ as directory
from yaner.utils.XDG import load_data_paths, load_config_paths
from yaner.utils.XDG import load_first_data, load_first_config
from yaner.utils.XDG import save_data_path, save_config_path

load_data_paths = partial(load_data_paths, directory)
load_config_paths = partial(load_config_paths, directory)
load_first_data = partial(load_first_data, directory)
load_first_config = partial(load_first_config, directory)
save_data_path = partial(save_data_path, directory)
save_config_path = partial(save_config_path, directory)
save_data_file = lambda filename: os.path.join(save_data_path(), filename)
save_config_file = lambda filename: os.path.join(save_config_path(), filename)

xdg_download_dir = os.environ.get('XDG_DOWNLOAD_DIR', os.path.expanduser('~'))

def xdg_open(args):
    args.insert(0, 'xdg-open')
    return subprocess.call(args)

