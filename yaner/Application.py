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
import sys
import logging
import argparse
import subprocess
from twisted.internet import reactor

from yaner import __version__
from yaner.Task import Task
from yaner.Constants import PREFIX, U_CONFIG_DIR, BUS_NAME
from yaner.ui.Dialogs import TaskNewDialog
from yaner.ui.Toplevel import Toplevel
from yaner.utils.Logging import LoggingMixin
from yaner.utils.Configuration import ConfigParser
from yaner.utils.UniqueApplication import UniqueApplicationMixin

class _VERSION(argparse.Action):
    """Show version information of the application."""

    def __call__(self, parser, namespace, values, option_string=None):
        print '{0} {1}'.format(__package__, __version__)
        print 'Copyright (C) 2010-2011 Iven (Xu Lijian)'
        print _('License GPLv3+: GNU GPL version 3 or later')
        print '<http://gnu.org/licenses/gpl.html>.'
        print _('This is free software:')
        print _('You are free to change and redistribute it.')
        print _('There is NO WARRANTY, to the extent permitted by law.')
        sys.exit(0)

class Application(UniqueApplicationMixin, LoggingMixin):
    """Main application of L{yaner}."""

    _NAME = __package__
    """The name of the application, used by L{_LOG_FILE}, etc."""

    _CONFIG_DIR = U_CONFIG_DIR
    """User config directory containing configuration files and log files."""

    _LOG_FILE = '{0}.log'.format(_NAME)
    """The logging file of the application."""

    _CONFIG_FILE = '{0}.conf'.format(_NAME)
    """The global configuration file of the application."""

    def __init__(self):
        """
        The init methed of L{Application} class.

        It handles command line options, creates L{toplevel window
        <Toplevel>}, and initialize logging configuration.
        """
        LoggingMixin.__init__(self)
        UniqueApplicationMixin.__init__(self, BUS_NAME)

        self._toplevel = None
        self._config = None

        self._init_logging()
        if len(sys.argv) > 1:
            self._init_args()

        # Set up and show toplevel window
        self.toplevel.show_all()

    @property
    def toplevel(self):
        """Get the toplevel window of L{yaner}."""
        if self._toplevel is None:
            self._toplevel = Toplevel(self.bus, self.config)
            self._toplevel.connect("destroy", self.quit)
        return self._toplevel

    @property
    def config(self):
        """
        Get the global configuration of the application.
        If the file doesn't exist, read from the default configuration.
        If the user configuration directory doesn't exist, create it.
        """
        if self._config is None:
            self.logger.info(_('Reading global configuration file...'))
            config = ConfigParser(self._CONFIG_DIR, self._CONFIG_FILE)
            if config.empty():
                self.logger.info(_('No global configuration file, creating...'))
                from yaner.Configurations import GLOBAL_CONFIG
                config.update(GLOBAL_CONFIG)
            self._config = config
        return self._config

    def on_instance_exists(self):
        """
        This method is called when an instance of the application
        already exists, which is required by L{UniqueApplicationMixin}.
        """
        if len(sys.argv) > 1:
            self._init_args(is_first_instance=False)
        else:
            print "Another instance is already running."
        sys.exit(0)

    def _init_args(self, is_first_instance=True):
        """Process command line arguments."""
        self.logger.info(_('Parsing command line arguments...'))
        self.logger.debug(_('Command line arguments: {0}').format(sys.argv))

        parser = argparse.ArgumentParser(
                description=_('{0} download mananger.').format(self._NAME))
        parser.add_argument('-n', '--rename', metavar='FILENAME',
                help=_('filename to save'))
        parser.add_argument('-r', '--referer', nargs='?', const='',
                default='', help=_('referer page of the link'))
        parser.add_argument('-c', '--cookie', nargs='?', const='',
                default='', help=_('cookies of the website'))
        parser.add_argument('uris', nargs='*', metavar='URI | MAGNET',
                help=_('the download addresses'))
        parser.add_argument('-v', '--version', action=_VERSION, nargs=0,
                help=_('output version information and exit'))
        args = parser.parse_args()

        self.logger.info(_('Command line arguments parsed.'))

        if is_first_instance:
            subprocess.Popen(sys.argv)
        else:
            options = {'referer': args.referer,
                    'header': args.cookie,
                    'uris': str(args.uris),
                    }
            if args.rename is not None:
                options['out'] = args.rename

            task_new_dialog = self.bus.get_object(
                    BUS_NAME, TaskNewDialog.OBJECT_NAME)
            task_new_dialog.run_dialog(Task.TYPES.NORMAL, options)

    def _init_logging(self):
        """Set up basic config for logging."""
        if not os.path.exists(self._CONFIG_DIR):
            os.makedirs(self._CONFIG_DIR)
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

