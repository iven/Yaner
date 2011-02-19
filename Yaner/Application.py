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
    This file contains the main application class of Yaner, mostly
GUI related.
"""

import gtk
import os, sys
import glob
import shutil
import subprocess
from twisted.internet import reactor

from Yaner.Constants import *
from Yaner.Constants import _
from Yaner.Server import ServerGroup, Server
from Yaner.Dialogs import TaskNewDialog, TaskProfileDialog
from Yaner.Task import TaskMixin
from Yaner.Configuration import ConfigFile
from Yaner.SingleInstance import SingleInstanceAppMixin

class YanerApp(SingleInstanceAppMixin):
    "Main Application"

    def __init__(self):
        SingleInstanceAppMixin.__init__(self, APP_BUS_NAME)
        # Init arguments
        self.__init_args()
        # Init paths
        self.__init_paths()
        # Init Config
        self.__init_confs()
        self.conf = ConfigFile.instances[U_MAIN_CONFIG_UUID]
        # Builder
        builder = gtk.Builder()
        builder.set_translation_domain('yaner')
        builder.add_from_file(MAIN_UI_FILE)
        builder.connect_signals(self)
        self.builder = builder
        # Main Window
        self.main_window = builder.get_object("main_window")
        self.__init_rgba(self.main_window)
        # Task List View
        self.tasklist_view = builder.get_object('tasklist_tv')
        selection = self.tasklist_view.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        # Server View
        server_tv = builder.get_object("server_tv")
        self.server_group = ServerGroup(self, server_tv)
        # Dialogs
        self.task_new_dialog = TaskNewDialog(self)
        self.task_profile_dialog = None
        # Popup Menu
        self.status_menu = builder.get_object("status_menu")
        # Show the window
        self.main_window.show()

    def __init_args(self, is_first_instance = True):
        """
        Init args.
        """
        args = sys.argv[1:]
        options = {}
        uris = []
        i = 0
        while(i < len(args)):
            if not args[i].startswith('-'):
                uris.append(args[i])
            elif args[i] in ('-h', '--help'):
                self.usage()
            elif args[i] in ('-v', '--version'):
                self.version()
            elif i + 1 < len(args) and not args[i + 1].startswith('-'):
                # Avoid something like '-r -c' to parse as {'-r': '-c'}
                if args[i] in ('-r', '--referer'):
                    options['referer'] = args[i + 1]
                elif args[i] in ('-c', '--cookie'):
                    options['header'] = 'Cookie: %s' % args[i + 1]
                elif args[i] in ('-n', '--rename'):
                    options['out'] = args[i + 1]
                else:
                    self.usage()
                i += 1
            i += 1
        if uris:
            if is_first_instance:
                # Run with the same options again
                subprocess.Popen(sys.argv)
            else:
                options['uris'] = '|'.join(uris)
                # Run task new dialog
                task_new_dialog = self.bus.get_object(
                        APP_BUS_NAME, TASK_NEW_DIALOG_OBJECT)
                task_new_dialog.run_dialog(TASK_NORMAL, options)

    @staticmethod
    def __init_rgba(window):
        """
        Init rgba.
        """
        screen = window.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap:
            gtk.widget_set_default_colormap(colormap)

    @staticmethod
    def __init_paths():
        """
        Create UConfigDir and config files during first start.
        """
        if not os.path.exists(U_CONFIG_DIR):
            os.makedirs(U_TASK_CONFIG_DIR)
            os.makedirs(U_CATE_CONFIG_DIR)
            os.makedirs(U_SERVER_CONFIG_DIR)
            shutil.copy(MAIN_CONFIG_FILE, U_CONFIG_DIR)
            shutil.copy(LOCAL_CATE_CONFIG_FILE, U_CATE_CONFIG_DIR)
            shutil.copy(LOCAL_SERVER_CONFIG_FILE, U_SERVER_CONFIG_DIR)

    @staticmethod
    def __init_confs():
        """
        Read config files during start.
        """
        conf_dirs = {
                U_CONFIG_DIR: '*.conf',
                U_TASK_CONFIG_DIR: '*',
                U_CATE_CONFIG_DIR: '*',
                U_SERVER_CONFIG_DIR: '*',
                }
        for (conf_dir, wildcard) in conf_dirs.iteritems():
            for conf_file in glob.glob(os.path.join(conf_dir, wildcard)):
                ConfigFile(conf_file)

    @staticmethod
    def __get_task_from_reference(reference):
        """
        Get Task class from a given reference.
        """
        model = reference.get_model()
        titer = model.get_iter(reference.get_path())
        task_uuid = model.get(titer, 9)[0]
        return TaskMixin.instances[task_uuid]

    def on_instance_exists(self):
        """
        Being called when another instance exists.
        """
        if len(sys.argv) > 1:
            self.__init_args(is_first_instance = False)
            sys.exit()
        else:
            SingleInstanceAppMixin.on_instance_exists(self)

    def get_task_new_dialog(self):
        """
        Get the task new dialog, if not existed, create it.
        """
        if self.task_new_dialog == None:
            self.task_new_dialog = TaskNewDialog(self)
        return self.task_new_dialog

    def get_task_profile_dialog(self):
        """
        Get the task profile dialog, if not existed, create it.
        """
        if self.task_profile_dialog == None:
            self.task_profile_dialog = TaskProfileDialog(self)
        return self.task_profile_dialog

    def on_task_new_action_activate(self, action):
        """
        Being called when task_new_action activated.
        """
        actions = (
                "task_new_normal_action",
                "task_new_bt_action",
                "task_new_metalink_action",
                )
        try:
            task_type = actions.index(action.get_property('name'))
        except ValueError:
            task_type = 0
        self.get_task_new_dialog().run_dialog(task_type)

    def on_task_profile_action_activate(self, action):
        """
        Being called when task_profile_action activated.
        """
        self.get_task_profile_dialog().run_dialog()

    def on_task_batch_action_activate(self, action):
        """
        Being called when task_start/pause/remove_action activated.
        """
        def start_task(reference):
            """
            Start downloading a task from given reference.
            If task is already started, unpause it.
            """
            task = self.__get_task_from_reference(reference)
            if task.conf.info.gid:
                task.unpause()
            else:
                task.start()

        def pause_task(reference):
            """
            Pause downloading a task from given reference.
            """
            task = self.__get_task_from_reference(reference)
            task.pause()

        def remove_task(reference):
            """
            Remove a task from given reference.
            """
            task = self.__get_task_from_reference(reference)
            task.remove()

        action_dict = {
                "task_start_action": start_task,
                "task_pause_action": pause_task,
                "task_remove_action": remove_task,
                }

        selection = self.tasklist_view.get_selection()
        (model, paths) = selection.get_selected_rows()
        references = [gtk.TreeRowReference(model, path) for path in paths]
        for reference in references:
            if reference.valid():
                action_dict[action.get_property('name')](reference)

    @staticmethod
    def on_about_action_activate(about_dialog):
        """
        Show about dialog.
        """
        about_dialog.set_version(VERSION)
        about_dialog.run()
        about_dialog.hide()

    @staticmethod
    def on_quit_action_activate(action):
        """
        Main window quit callback.
        """
        # Kill local aria2c process
        Server.instances[LOCAL_SERVER_UUID].server_process.terminate()
        gtk.widget_pop_colormap()
        reactor.stop()

    @staticmethod
    def on_main_window_delete_event(window, event):
        """
        When close button is pressed, minimize the window.
        """
        window.hide()
        return True

    def on_statusicon_button_press_event(self, status_icon, event):
        """
        Button press event handler of the status icon.
        If user double clicks the icon, just show/hide the window.
        """
        if event.type == gtk.gdk._2BUTTON_PRESS:
            window = self.main_window
            if window.get_property('visible'):
                window.hide()
            else:
                window.present_with_time(event.time)
        elif event.button == 3:
            self.status_menu.popup(None, None,
                    gtk.status_icon_position_menu,
                    event.button, event.time, status_icon)
        return False

    @staticmethod
    def usage(err = ''):
        """
        Print help messages and exit.
        """
        # Print errors
        if err:
            print _('Error: %s') % err
            print
        # Print usage and options
        opts = (('-n FILE, --rename FILE', _('filename to save')),
            ('-r URI, --referer URI', _('referer page of the link')),
            ('-c COOKIE, --referer COOKIE',_('cookies of the website')),
            ('-h, --help', _('display this help and exit')),
            ('-v, --version', _('output version information and exit')))
        print _('Usage: yaner [OPTION]... [URI | MAGNET]...')
        print
        print _('Options:')
        for (opt, des) in opts:
            print '  %-28s%s' % (opt, des)
        sys.exit(0)

    @staticmethod
    def version():
        """
        Print version information and exit.
        """
        print "yaner %s" % VERSION
        print 'Copyright (C) 2010 Iven Day (Xu Lijian)'
        print _("License GPLv3+: GNU GPL version 3 or later"),
        print '<http://gnu.org/licenses/gpl.html>.'
        print _("This is free software:"),
        print _("you are free to change and redistribute it.")
        print _("There is NO WARRANTY, to the extent permitted by law.")
        sys.exit(0)

if __name__ == '__main__':
    YanerApp()
    gtk.main()
