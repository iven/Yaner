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
import logging

from gi.repository import Gtk, GLib, Gio
from sqlalchemy import create_engine

from yaner import __package__
from yaner import SQLSession, SQLBase
from yaner.XDG import save_data_file
from yaner.Pool import Pool
from yaner.Presentable import Category
from yaner.Constants import APPLICATION_ID
from yaner.ui.Toplevel import Toplevel
from yaner.utils.Logging import LoggingMixin

class Application(Gtk.Application, LoggingMixin):
    """Main application of L{yaner}."""

    _NAME = __package__
    """The name of the application, used by L{_LOG_FILE}, etc."""

    _LOG_FILE = '{0}.log'.format(_NAME)
    """The logging file of the application."""

    _DATA_FILE = '{}.db'.format(_NAME)
    """The global database file of the application."""

    def __init__(self):
        """
        The init methed of L{Application} class.

        It handles command line options, creates L{toplevel window
        <Toplevel>}, and initialize logging configuration.
        """
        Gtk.Application.__init__(self, application_id=APPLICATION_ID, flags=0)
        LoggingMixin.__init__(self)

        self._toplevel = None
        self._settings = None

        self._init_action_group()

    @property
    def toplevel(self):
        """Get the toplevel window of L{yaner}."""
        if self._toplevel is None:
            self._toplevel = Toplevel()
        return self._toplevel

    @property
    def settings(self):
        """Get the GSettings object."""
        if self._settings is None:
            self._settings = Gio.Settings('com.kissuki.yaner')
        return self._settings

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
        self.logger.info(_('Logging system initialized, start logging...'))

    def _init_database(self):
        """Connect to database and set up database if this is the first
        start of the application."""
        self.logger.info(_('Connecting to global database file...'))

        data_file = save_data_file(self._DATA_FILE)
        engine = create_engine('sqlite:///' + data_file)
        SQLSession.configure(bind=engine)

        if not os.path.exists(data_file):
            self.logger.info(_('Initializing database for first start...'))

            SQLBase.metadata.create_all(engine)

            pool = Pool(name=_('My Computer'), host='localhost', is_local=True)

            docs_dir = os.environ.get('XDG_DOCUMENTS_DIR', os.path.expanduser('~'))
            Category(name=_('Documents'), directory=docs_dir, pool=pool)

            videos_dir = os.environ.get('XDG_VIDEOS_DIR', os.path.expanduser('~'))
            Category(name=_('Videos'), directory=videos_dir, pool=pool)

            music_dir = os.environ.get('XDG_MUSIC_DIR', os.path.expanduser('~'))
            Category(name=_('Music'), directory=music_dir, pool=pool)

            self.logger.info(_('Database initialized.'))

        self.logger.info(_('Global database file connected.'))

    def _init_action_group(self):
        """Insert 'cmdline' action for opening new task dialog."""
        action_group = Gio.SimpleActionGroup()
        action = Gio.SimpleAction.new(name='cmdline',
                                      parameter_type=GLib.VariantType.new('s'))
        action.connect('activate', self.on_cmdline)
        action_group.insert(action)
        self.set_action_group(action_group)

    def _init_first_start(self):
        """If it's first start, ask for starting daemon on system startup."""
        if self.settings.get_boolean('first-start'):
            message = _("It seems it's the first time you run Yaner. "
                        "Yaner requires a daemon to run background, which is "
                        "highly recommended to be started on system startup.\n\n"
                        "Do you want to run it on system startup?\n"
                        "(Or run it everytime yourself: "
                        "$ aria2c --enable-rpc --allow-overwrite)")
            dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.QUESTION,
                                       Gtk.ButtonsType.YES_NO, message,
                                       title=_('Welcome to Yaner!'))
            response = dialog.run()
            dialog.destroy()

            if response == Gtk.ResponseType.YES:
                import subprocess
                from yaner.utils.XDG import load_first_config, save_config_path

                in_path = load_first_config('autostart/yaner-daemon.desktop')
                out_path = os.path.join(save_config_path('autostart'),
                                        'yaner-daemon.desktop')
                if in_path != out_path:
                    with open(in_path) as f_in, open(out_path, 'w') as f_out:
                        lines = [line for line in f_in
                                 if not line.startswith('Hidden')]
                        f_out.writelines(lines)
                    subprocess.Popen(['aria2c', '--enable-rpc', '--allow-overwrite'],
                                     stdout=subprocess.PIPE)

            self.settings.set_boolean('first-start', False)

    def on_cmdline(self, action, data):
        """When application started with command line arguments, open new
        task dialog.
        """
        options = eval(data.unpack())
        self.logger.info(_('Received task options from command line arguments.'))
        self.logger.debug(str(options))

        dialog = self.toplevel.normal_task_new_dialog
        dialog.run(options)

    def do_activate(self):
        """When Application activated, present the main window."""
        self.logger.debug(_('Activating toplevel window...'))
        self.toplevel.present()

    def do_startup(self):
        """When start up, initialize logging and database systems, and
        show the toplevel window.
        """
        self._init_logging()
        self._init_first_start()
        self._init_database()
        self.toplevel.set_application(self)
        self.toplevel.show_all()

    def do_shutdown(self):
        """When shutdown, finalize database and logging systems."""
        self.logger.info(_('Shutting down database...'))
        SQLSession.commit()
        SQLSession.close()

        self.logger.info(_('Application quit normally.'))
        logging.shutdown()

