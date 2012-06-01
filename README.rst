======================
Yaner Download Manager
======================

*Yaner* is a download manager written in Python 3 and pygobject. Actually it's just
a client(or GUI wrapper) for *aria2*, the famous CLI download utility, which
supports HTTP(s), FTP, BitTorrent(including Magnet), and Metalink. Sure, Yaner
supports these all.

Still under development and unstable, but won't eat your cat. If you find it
doesn't work properly after an update, just try to remove ``~/.config/yaner/`` and
``~/.local/share/yaner/``.

Features
========

* (Almostly) all features aria2 supports.
* Pretty simple, straight toward UI.
* Control your downloads remotely.
* Multiple aria2 download servers, and multiple task categories for each server.
* A smart and handsome author.

Dependencies
============

Build
-----

* python-distutils-extra

Runtime
-------

* Python >= 3.2.0
* PyGObject
* GTK3
* dconf
* libnotify
* SQLAlchemy >= 0.7.0
* python-chardet
* xdg-utils

Install
=======

Run the setup.py script as root to install, e.g.::

    python3 setup.py install

If you use Debian/Ubuntu based distributions, you should install like this::

    python3 setup.py install --install-layout=deb

After that, run this as root::

    glib-compile-schemas /usr/share/glib-2.0/schemas/
    gtk-update-icon-cache -qtf /usr/share/icons/hicolor/

Browser support
===============

For Firefox, install FlashGot, add a new DM in the preferences dialog::

    Executable path: /usr/bin/yaner
    Command line:    [URL] [--referer REFERER] [--rename FNAME] [--cookie COOKIE]

Other browers are currently not supported.

