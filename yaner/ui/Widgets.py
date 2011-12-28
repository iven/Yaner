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

import collections

from gi.repository import Gtk, GObject

class AlignedExpander(Gtk.Expander):
    """A L{Gtk.Expander} with an alignment that can place its children nicely."""
    def __init__(self, markup, expanded=True):
        Gtk.Expander.__init__(self, label=markup, use_markup=True,
                              resize_toplevel=True, expanded=expanded)

        self.alignment = Gtk.Alignment()
        self.alignment.set_padding(0, 0, 12, 5)
        Gtk.Expander.add(self, self.alignment)

    def add(self, child):
        """Add child to alignment."""
        self.alignment.add(child)

class URIsView(Gtk.ScrolledWindow):
    """ScrolledWindow with a text view for getting/setting URIs."""

    def __init__(self):
        Gtk.ScrolledWindow.__init__(
            self, None, None, shadow_type=Gtk.ShadowType.IN,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self.set_size_request(-1, 70)

        text_view = Gtk.TextView(accepts_tab=False, wrap_mode=Gtk.WrapMode.CHAR)
        self.add(text_view)

        text_buffer = text_view.get_buffer()
        text_buffer.connect('changed', self._text_changed)
        self.text_buffer = text_buffer

    def _text_changed(self, text_buffer):
        """When text in the buffer changed, update uris property."""
        self.notify('uris')

    def get_uris(self):
        tbuffer = self.text_buffer
        return tbuffer.get_text(
            tbuffer.get_start_iter(),
            tbuffer.get_end_iter(),
            False
            ).split()

    def set_uris(self, uris):
        tbuffer = self.text_buffer
        if isinstance(uris, str):
            tbuffer.set_text(uris)
        elif isinstance(uris, collections.Sequence):
            tbuffer.set_text('\n'.join(uris))
        else:
            raise TypeError('URIs should be a string or sequence.')

    uris = GObject.property(getter=get_uris, setter=set_uris)

class MetafileChooserButton(Gtk.FileChooserButton):
    """A single file chooser button with a file filter."""

    filename = GObject.property(getter=Gtk.FileChooserButton.get_filename)

    def __init__(self, title, mime_types):
        Gtk.FileChooserButton.__init__(self, title=title)

        file_filter = Gtk.FileFilter()
        for mime_type in mime_types:
            file_filter.add_mime_type(mime_type)

        self.set_filter(file_filter)

    def do_file_set(self):
        """When the file selected, update filename property."""
        self.notify('filename')

class FileChooserEntry(Gtk.Entry):
    """An Entry with a activatable icon that popups FileChooserDialog."""

    def __init__(self, title, parent, file_chooser_action):
        Gtk.Entry.__init__(self)

        self.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, 'gtk-directory')
        self.connect('icon-press', self._on_icon_press)

        dialog = Gtk.FileChooserDialog(
            title, parent, file_chooser_action,
            [Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT]
            )
        dialog.set_transient_for(parent)
        self._file_chooser_dialog = dialog

    def _on_icon_press(self, entry, icon_pos, event):
        """When icon activated, popup file chooser dialog."""
        if icon_pos == Gtk.EntryIconPosition.SECONDARY:
            dialog = self._file_chooser_dialog
            if dialog.run() == Gtk.ResponseType.ACCEPT:
                self.set_text(dialog.get_filename())
            dialog.hide()

