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

from yaner.Configuration import ConfigFile
from yaner.Task import TASK_CLASSES

class Category:
    """
    Category class. Each category contains several tasks and a saving
    directory.
    """

    instances = {}

    def __init__(self, cate_uuid):
        self.uuid = cate_uuid
        self.citer = None

        # Add self to the global dict
        self.instances[self.uuid] = self

    def get_conf(self):
        """
        Get category ConfigFile.
        """
        return ConfigFile.instances[self.uuid]

    def get_task_uuids(self):
        """
        Get server task uuids.
        """
        task_uuids = self.get_conf().info.tasks.split(',')
        return task_uuids if task_uuids != [''] else []

    def get_tasks(self):
        """
        Get category task instances.
        """
        return (TaskMixin.instances[task_uuid]
                for task_uuid in self.get_task_uuids())

    def get_name(self):
        """
        Get category name.
        """
        return self.get_conf().info.name

    def set_iter(self, cate_iter):
        """
        Set category iter.
        """
        self.citer = cate_iter

    def add_task(self, info, options, conf = None, is_new = True):
        """
        Add task to category, from info + options, or conf.
        If a task is new added to the category, is_new should be True.
        if we just want to display an existing task on the server, is_new will be False.
        """
        if info != None and options != None:
            # Must be new task, generate a conf file for it.
            task_uuid = str(uuid.uuid1())
            task_conf = ConfigFile(os.path.join(U_TASK_CONFIG_DIR, task_uuid))
            info['uuid'] = task_uuid
            task_conf['info'] = info
            task_conf['options'] = options

        TASK_CLASSES[int(conf.info.type)](self, conf, is_new)

