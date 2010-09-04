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
    This file contains classes about download categories.
"""

import os

from Yaner.Constants import *
from Yaner.Task import TaskMixin, TASK_CLASSES
from Yaner.Configuration import ConfigFile

class Category:
    """
    Category class. Each category contains several tasks and a saving
    directory.
    """

    instances = {}

    def __init__(self, server, cate_uuid):
        self.server = server
        self.uuid = cate_uuid
        self.conf = ConfigFile.instances[self.uuid]
        self.citer = None

        # Add self to the global dict
        self.instances[self.uuid] = self

    def get_task_uuids(self):
        """
        Get server task uuids.
        """
        task_uuids = self.conf.info.tasks.split(',')
        return task_uuids if task_uuids != [''] else []

    def set_task_uuids(self, task_uuids):
        """
        Set server task uuids.
        task_uuids is a tuple.
        """
        self.conf.info['tasks'] = ','.join(task_uuids)

    def add_task_uuid(self, task_uuid):
        """
        Add a task uuid to config file.
        """
        task_uuids = self.get_task_uuids()
        task_uuids.append(task_uuid)
        self.set_task_uuids(task_uuids)

    def remove_task_uuid(self, task_uuid):
        """
        Remove a task uuid from the config file.
        """
        task_uuids = self.get_task_uuids()
        task_uuids.remove(task_uuid)
        self.set_task_uuids(task_uuids)

    def get_tasks(self):
        """
        Get category task instances.
        """
        return [TaskMixin.instances[task_uuid]
                for task_uuid in self.get_task_uuids()]

    def get_name(self):
        """
        Get category name.
        """
        return self.conf.info.name

    def get_dir(self):
        """
        Get category directory.
        """
        return self.conf.info.dir

    def set_iter(self, cate_iter):
        """
        Set category iter.
        """
        self.citer = cate_iter

    def add_task(self, info, options, conf = None):
        """
        Add task to category, from info + options, or conf.
        """
        is_new_task = (info != None) and (options != None)
        if is_new_task:
            # Must be new task, generate a conf file for it.
            task_uuid = info['uuid']
            conf = ConfigFile(os.path.join(U_TASK_CONFIG_DIR, task_uuid))
            conf['info'] = info
            conf['options'] = options
            # Add task uuid to category config file
            self.add_task_uuid(task_uuid)
        task = TASK_CLASSES[int(conf.info.type)](self, conf)
        if is_new_task:
            task.start()

    def remove_task(self, task):
        self.remove_task_uuid(task.uuid)

