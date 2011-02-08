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
This module contains the main application class of L{yaner}.
"""

import os
import logging
from gettext import gettext as _
from twisted.internet import reactor
from xdg.BaseDirectory import xdg_config_home

from Constants import PREFIX, CONFIG_DIR
from ui.Toplevel import Toplevel
from utils.UniqueApplication import UniqueApplicationMixin
from utils.I18nApplication import I18nApplicationMixin
from utils.Logging import LoggingMixin

class Application(UniqueApplicationMixin, I18nApplicationMixin, LoggingMixin):
    """Main application of L{yaner}."""

    _NAME = __package__
    """
    The name of the application, used by L{_BUS_NAME}, etc.
    """

    _BUS_NAME = 'com.kissuki.{}'.format(_NAME)
    """
    The unique bus name of the application, which identifies
    the application when using DBus to implement the
    L{UniqueApplicationMixin} class.
    """

    _CONFIG_DIR = os.path.join(xdg_config_home, _NAME)
    """
    User config directory where saves configuration files and log files.
    """

    _LOG_FILE = '{}.log'.format(_NAME)
    """The logging file of the application."""

    _CONFIG_FILE = '{}.conf'.format(_NAME)
    """The global configuration file of the application."""

    def __init__(self):
        """
        The init methed of L{Application} class.

        It handles command line options, creates L{toplevel window
        <Toplevel>}, and initialize logging configuration.
        """
        UniqueApplicationMixin.__init__(self, self._BUS_NAME)
        I18nApplicationMixin.__init__(self, self._NAME, PREFIX)
        LoggingMixin.__init__(self)

        self._init_logging()

        # Set up toplevel window
        self._toplevel = Toplevel()
        self._toplevel.show_all()
        self._toplevel.connect("destroy", self.quit)

    @property
    def toplevel(self):
        """Get the toplevel window of L{yaner}."""
        return self._toplevel

    @staticmethod
    def on_instance_exists():
        """
        This method is called when an instance of the application
        already exists, which is required by L{UniqueApplicationMixin}.
        """
        print "Another instance is already running."
        import sys
        sys.exit(0)

    def _init_logging(self):
        """Set up basic config for logging."""
        formatstr = ' '.join((
            '%(levelname)-8s',
            '%(name)s.%(funcName)s,',
            'L%(lineno)-3d:',
            '%(message)s'
            ))
        logging.basicConfig(
            filename = os.path.join(self._CONFIG_DIR, self._LOG_FILE),
            filemode = 'w',
            format = formatstr,
            level = logging.DEBUG
            )
        self.logger.info(_('Logging system initialized, start logging...'))

    def quit(self, *arg, **kwargs):
        """
        The callback function of the I{destory} signal of L{toplevel}.
        Just quit the application.
        """
        self.logger.info(_('Application quit normally.'))
        logging.shutdown()
        reactor.stop()

    @staticmethod
    def run():
        """Run the main loop of the application."""
        reactor.run()

