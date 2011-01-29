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
This module contains the global constants of L{yaner}.
"""

DATA_DIR = "@prefix@/share/yaner"
"""
The global data directory of L{yaner}, which contains default
configurations, ui related files, icons, etc.
"""

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
This module contains the global constants of L{yaner}.
"""

from os.path import join as _join
from xdg.BaseDirectory import xdg_config_home as _config_home

PREFIX = "@prefix@"
"""The install prefix, usually "I{/usr}" or "I{/usr/local}"."""

DATA_DIR = _join(PREFIX, "share/{0}".format(__package__))
"""
The global data directory of L{yaner}, which contains default
configurations, ui related files, icons, etc.
"""

U_CONFIG_DIR = _join(_config_home, __package__)
"""
User config directory where saves configuration files and log files.
"""

