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
This module contains the default configuration dicts of L{yaner}.
"""

import os

GLOBAL_CONFIG = {
        'info': {
            'pools': ['ea1ab4a7-6973-4b7b-8cb0-09e11ab42a14'],
            },
        'global': {
            'max-overall-download-limit': 0,
            'max-overall-upload-limit': 0,
            },
        'task': {
            'dir': '',
            'out': '',
            'split': 5,
            'referer': '',
            'all-proxy': '',
            'auto-file-renaming': 'true',

            'http-user': '',
            'http-passwd': '',
            'ftp-user': '',
            'ftp-passwd': '',
            'http-proxy-user': '',
            'http-proxy-passwd': '',
            'ftp-proxy-user': '',
            'ftp-proxy-passwd': '',

            'connect-timeout': 60,
            'timeout': 60,
            'max-tries': 5,
            'max-file-not-found': 5,
            'max-connection-per-server': 3,

            'follow-torrent': 'false',
            'follow-metalink': 'false',
            'seed-time': 120,
            'seed-ratio': 2.00,
            'bt-max-open-files': 100,
            'bt-max-peers': 55,
            'bt-tracker-connect-timeout': 60,
            'bt-tracker-timeout': 60,
            'bt-prioritize-piece': ['head', 'tail'],

            'metalink-servers': 5,
            'metalink-language': '',
            'metalink-location': '',
            'metalink-os': '',
            'metalink-version': '',
            }
        }
"""The global configuration dict of the application."""

POOL_CONFIG = {
        'info': {
            'name': _("My Computer"),
            'host': 'localhost',
            'port': 6800,
            'user': '',
            'passwd': '',
            'session_id': '',
            'queuing': '',
            'categories': [''],
            'dustbin': '',
            },
        }
"""The pool configuration dict of the application."""

QUEUING_CONFIG = {
        'info': {
            'tasks': [],
            },
        }
"""The queuing configuration dict of the application."""

CATEGORY_CONFIG = {
        'info': {
            'name': _("Default Category"),
            'dir': os.path.expanduser('~'),
            'tasks': [],
            },
        }
"""The category configuration dict of the application."""

DUSTBIN_CONFIG = {
        'info': {
            'tasks': [],
            },
        }
"""The dustbin configuration dict of the application."""

TASK_CONFIG = {
        'info': {
            'size': 0,
            },
        'options': {
            'all-proxy': '',
            'http-proxy-user': '',
            'http-proxy-passwd': '',
            'ftp-proxy-user': '',
            'ftp-proxy-passwd': '',
            'connect-timeout': 60,
            'timeout': 60,
            'max-file-not-found': 5,
            'max-tries': 5,
            'split': 5,
            'auto-file-renaming': 'true',
            'max-connection-per-server': 3,
            'follow-torrent': 'false',
            'follow-metalink': 'false',
            'seed-time': 120,
            'seed-ratio': 2.00,
            'bt-max-open-files': 100,
            'bt-max-peers': 55,
            'bt-tracker-connect-timeout': 60,
            'bt-tracker-timeout': 60,
            'metalink-servers': 5,
            'metalink-language': '',
            'metalink-location': '',
            'dir': '',
            'referer': '',
            'out': '',
            'http-user': '',
            'http-passwd': '',
            'ftp-user': '',
            'ftp-passwd': '',
            'bt-prioritize-piece': 'head,tail',
            'metalink-os': '',
            'metalink-version': '',
            },
        }
"""The task configuration dict of the application."""
