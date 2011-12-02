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

"""This module contains some widgets for common use."""

from gi.repository import Gtk

class AlignedFrame(Gtk.Frame):
    """A L{Gtk.Frame} with no shadow, and with an alignment that can place its
    children nicely.
    """
    def __init__(self, label):
        Gtk.Frame.__init__(self, shadow_type=Gtk.ShadowType.NONE)

        label = Gtk.Label(label='<b>{}</b>'.format(label), use_markup=True)
        self.set_label_widget(label)

        self.alignment = Gtk.Alignment()
        self.alignment.set_padding(5, 5, 12, 5)
        Gtk.Frame.add(self, self.alignment)

    def add(self, child):
        """Add child to alignment."""
        self.alignment.add(child)

