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

import functools
import collections

from gi.repository import Gtk

HORIZONTAL, VERTICAL = Gtk.Orientation.HORIZONTAL, Gtk.Orientation.VERTICAL

LeftAlignedLabel = functools.partial(Gtk.Label, xalign=0)

class Box(Gtk.Box):
    """Simplified Gtk.Box."""
    def __init__(self, orientation, spacing=5, *args, **kwargs):
        Gtk.Box.__init__(self, orientation=orientation,
                         spacing=spacing, *args, **kwargs)

        self.pack_start = functools.partial(self.pack_start,
                                            expand=True, fill=True, padding=0)
        self.pack_end = functools.partial(self.pack_end,
                                          expand=True, fill=True, padding=0)

class AlignedExpander(Gtk.Expander):
    """A L{Gtk.Expander} with an alignment that can place its children nicely."""
    def __init__(self, label='', expanded=True):
        Gtk.Expander.__init__(self, label=label, use_markup=True,
                              resize_toplevel=True, expanded=expanded)

        alignment = Gtk.Alignment()
        alignment.set_padding(0, 0, 12, 5)
        Gtk.Expander.add(self, alignment)

        self.add = alignment.add
        self.remove = alignment.remove
        self.get_child = alignment.get_child

class Entry(Gtk.Entry):
    """An entry for using to store settings."""
    @property
    def value(self):
        return self.get_text()

    @value.setter
    def value(self, value):
        self.set_text(value)

class SpinButton(Gtk.SpinButton):
    """An spin button for using to store settings."""
    @property
    def value(self):
        return self.get_value()

    @value.setter
    def value(self, value):
        self.set_value(value)

class Switch(Gtk.Switch):
    """An switch for using to store settings."""
    @property
    def value(self):
        return self.get_active()

    @value.setter
    def value(self, value):
        self.set_active(value)

class URIsView(Gtk.ScrolledWindow):
    """ScrolledWindow with a text view for getting/setting URIs."""

    def __init__(self):
        Gtk.ScrolledWindow.__init__(
            self, None, None, shadow_type=Gtk.ShadowType.IN,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)

        text_view = Gtk.TextView(accepts_tab=False, wrap_mode=Gtk.WrapMode.CHAR)
        self.add(text_view)
        self.text_view = text_view

        text_buffer = text_view.get_buffer()
        self.text_buffer = text_buffer

    @property
    def value(self):
        tbuffer = self.text_buffer
        return tbuffer.get_text(
            tbuffer.get_start_iter(),
            tbuffer.get_end_iter(),
            False
            ).split()

    @value.setter
    def value(self, uris):
        tbuffer = self.text_buffer
        if isinstance(uris, str):
            tbuffer.set_text(uris)
        elif isinstance(uris, collections.Sequence):
            tbuffer.set_text('\n'.join(uris))
        else:
            raise TypeError('URIs should be a string or sequence.')

    def grab_focus(self):
        self.text_view.grab_focus()

class MetafileChooserButton(Gtk.FileChooserButton):
    """A single file chooser button with a file filter."""

    def __init__(self, title, mime_types):
        Gtk.FileChooserButton.__init__(self, title=title)

        file_filter = Gtk.FileFilter()
        for mime_type in mime_types:
            file_filter.add_mime_type(mime_type)

        self.set_filter(file_filter)

    @property
    def value(self):
        return self.get_filename()

    @value.setter
    def value(self, value):
        self.set_filename(value)

class FileChooserEntry(Entry):
    """An Entry with a activatable icon that popups FileChooserDialog."""

    def __init__(self, title, parent, file_chooser_action, update_entry=True,
                 mime_list=None, **kwargs):
        Entry.__init__(self, **kwargs)

        self.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, 'gtk-open')
        self.connect('icon-press', self._on_icon_press)

        dialog = Gtk.FileChooserDialog(
            title, parent, file_chooser_action,
            [Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT]
            )
        dialog.set_transient_for(parent)
        self._file_chooser_dialog = dialog

        if mime_list is not None:
            for mime_item in mime_list:
                file_filter = Gtk.FileFilter()
                file_filter.set_name(mime_item[0])
                for mime_type in mime_item[1]:
                    file_filter.add_mime_type(mime_type)
                dialog.add_filter(file_filter)

        # Update the entry text when file choosed?
        if update_entry:
            dialog.connect('response', self._update_directory_path)

    def _on_icon_press(self, entry, icon_pos, event):
        """When icon activated, popup file chooser dialog."""
        if icon_pos == Gtk.EntryIconPosition.SECONDARY:
            dialog = self._file_chooser_dialog
            dialog.run()
            dialog.hide()

    def _update_directory_path(self, dialog, response_id):
        """When file choosed, update the entry text."""
        if response_id == Gtk.ResponseType.ACCEPT:
            self.set_text(dialog.get_filename())

    def connect(self, signal_name, *args, **kwargs):
        if signal_name in ('response'):
            self._file_chooser_dialog.connect(signal_name, *args, **kwargs)
        else:
            Gtk.Entry.connect(self, signal_name, *args, **kwargs)

