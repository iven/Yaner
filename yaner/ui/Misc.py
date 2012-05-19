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
This module contains miscellaneous functions used by other modules.
"""

import os
import logging

from gi.repository import Gtk

from yaner.ui import __package__

_module = '{0}.Misc'.format(__package__)
_logger = logging.getLogger(_module)

def load_ui_file(filename):
    """Get the UI file path by filename."""
    directory = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(directory, filename)

def get_mix_color(widget, state):
    """
    Get lighter color than the normal text color, which is mixed with
    M{textcolor * 0.7 + basecolor * 0.3}.
    @arg widget:The widget where the text display on.
    @type widget:C{Gtk.Widget}
    @arg state:Current state of the L{widget}.
    @type state:C{int}
    """
    try:
        if not isinstance(widget, Gtk.Widget):
            raise TypeError
    except TypeError:
        _logger.exception("@widget is not a Gtk.Widget.")
        return 'gray'

    color = {}
    style = widget.get_style()
    for component in ('red', 'green', 'blue'):
        color[component] = int(
                getattr(style.text[state], component) * 0.7 +
                getattr(style.base[state], component) * 0.3
                )
    color = '#{red:02X}{green:02X}{blue:02X}'.format(**color)
    #_logger.debug("Got mix color: {0}.".format(color))

    return color

