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
This module contains the main application class of L{yaner}.
"""

import os
import sys
import logging
import argparse
import subprocess

from PyQt4.QtGui import QApplication, QLabel
from PyQt4.QtCore import QLocale, QTranslator, QLibraryInfo, QTimer
from gi.repository import Notify

from sqlalchemy import create_engine

from yaner.XDG import save_data_file
from yaner.Misc import VersionAction
from yaner.Pool import Pool
from yaner.Database import SQLSession, SQLBase
from yaner.Presentable import Category
#from yaner.ui.Toplevel import Toplevel
from yaner.utils.Logging import LoggingMixin

class Application(QApplication, LoggingMixin):
    _NAME = "Yaner"
    """The name of the application, used by L{_LOG_FILE}, etc."""

    _LOG_FILE = '{}.log'.format(_NAME)
    """The logging file of the application."""

    _DATA_FILE = '{}.db'.format(_NAME)
    """The global database file of the application."""

    _SYNC_INTERVAL = 60000
    """Interval for database sync, in millisecond(s)."""

    def __init__(self, argv):
        QApplication.__init__(self, argv)
        LoggingMixin.__init__(self)

        self._translators = {}
        self._daemon = None
        self._main_window = None
        self._database_sync_timer = None

        self._init_i18n()
        self._init_args(argv)
        self._init_logging()
        self._init_database()
        self._init_daemon()

        Notify.init('yaner')

        self.label = QLabel(self.tr('yaner'))
        self.label.show()

        self.aboutToQuit.connect(self.on_about_to_quit)

    @property
    def database_sync_timer(self):
        if self._database_sync_timer is None:
            timer = QTimer()
            timer.setInterval(self._SYNC_INTERVAL)
            timer.timeout.connect(SQLSession.commit)
            self._database_sync_timer = timer
        return self._database_sync_timer

    @property
    def main_window(self):
        """Get the toplevel window of L{yaner}."""
        # TODO
        #if self._main_window is None:
        #    self._main_window = MainWindow()
        return self._main_window

    def _init_args(self, argv):
        """Parse command line arguments."""
        options = None
        if len(argv) > 1:
            parser = argparse.ArgumentParser(
                    description=self.tr('Yaner download mananger.'))
            parser.add_argument('-n', '--rename', metavar='FILENAME',
                    help=self.tr('filename to save'))
            parser.add_argument('-r', '--referer', nargs='?', const='',
                    default='', help=self.tr('referer page of the link'))
            parser.add_argument('-c', '--cookie', nargs='?', const='',
                    default='', help=self.tr('cookies of the website'))
            parser.add_argument('uris', nargs='*', metavar='URI | MAGNET',
                    help=self.tr('the download addresses'))
            parser.add_argument('-v', '--version', action=VersionAction, nargs=0,
                    help=self.tr('output version information and exit'))
            args = parser.parse_args()

            options = {'referer': args.referer,
                       'header': 'Cookie: {}'.format(args.cookie),
                       'uris': '\n'.join(args.uris),
                      }
            if args.rename is not None:
                options['out'] = args.rename

        if options is not None:
            print(options)
            sys.exit()

    def _init_i18n(self):
        """Set up Qt translater."""
        locale = QLocale.system().name()
        tr_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)

        translator = QTranslator()
        if translator.load('qt_' + locale, tr_path):
            self.installTranslator(translator)
        self._translators['qt'] = translator

        translator = QTranslator()
        if translator.load('yaner_' + locale, '.'):
            self.installTranslator(translator)
        self._translators['application'] = translator

    def _init_logging(self):
        """Set up basic config for logging."""
        formatstr = ' '.join((
            '%(levelname)-8s',
            '%(name)s.%(funcName)s,',
            'L%(lineno)-3d:',
            '%(message)s'
            ))
        logging.basicConfig(
            #filename = save_config_file(self._LOG_FILE),
            filemode = 'w',
            format = formatstr,
            level = logging.DEBUG
            )
        self.logger.info('Logging system initialized, start logging...')

    def _init_database(self):
        """Connect to database and set up database if this is the first
        start of the application."""
        self.logger.info('Connecting to global database file...')

        data_file = save_data_file(self._DATA_FILE)
        engine = create_engine('sqlite:///' + data_file)
        SQLSession.configure(bind=engine)

        if not os.path.exists(data_file):
            self.logger.info('Initializing database for first start...')

            SQLBase.metadata.create_all(engine)

            pool = Pool(name=self.tr('My Computer'), host='localhost', is_local=True)

            docs_dir = os.environ.get('XDG_DOCUMENTS_DIR', os.path.expanduser('~'))
            Category(name=self.tr('Documents'), directory=docs_dir, pool=pool)

            videos_dir = os.environ.get('XDG_VIDEOS_DIR', os.path.expanduser('~'))
            Category(name=self.tr('Videos'), directory=videos_dir, pool=pool)

            music_dir = os.environ.get('XDG_MUSIC_DIR', os.path.expanduser('~'))
            Category(name=self.tr('Music'), directory=music_dir, pool=pool)

            self.logger.info('Database initialized.')

        # Auto commit to database
        self.database_sync_timer.start()

        self.logger.info('Global database file connected.')

    def _init_daemon(self):
        """Start aria2 daemon on start up."""
        self._daemon = subprocess.Popen(['aria2c', '--enable-rpc'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                       )

    def on_about_to_quit(self):
        """When shutdown, finalize database and logging systems."""
        self.logger.info('Shutting down database...')
        SQLSession.commit()
        SQLSession.close()

        self._daemon.terminate()

        self.logger.info('Application quit normally.')
        logging.shutdown()

