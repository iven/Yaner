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
This module contains miscellaneous functions used by other modules.
"""

import gtk
import logging
from gettext import gettext as _

_module = '{}.Misc'.format(__package__)
_logger = logging.getLogger(_module)

def get_mix_color(widget, state):
    """
    Get lighter color than the normal text color, which is mixed with
    M{textcolor * 0.7 + basecolor * 0.3}.
    @arg widget:The widget where the text display on.
    @type widget:C{gtk.Widget}
    @arg state:Current state of the L{widget}.
    @type state:C{int}
    """
    try:
        if not isinstance(widget, gtk.Widget):
            raise TypeError
    except TypeError:
        _logger.exception(_("@widget is not a gtk.Widget."))
        return 'gray'

    color = {}
    style = widget.get_style()
    for component in ('red', 'green', 'blue'):
        color[component] = int(
                getattr(style.text[state], component) * 0.7 +
                getattr(style.base[state], component) * 0.3
                )
    color = '#{red:02X}{green:02X}{blue:02X}'.format(**color)
    _logger.debug(_("Got mix color: {}.").format(color))

    return color

