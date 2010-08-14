#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Yaner.

# Yaner - GTK+ interface for aria2 download mananger
# Copyright (C) 2010  Iven Day <ivenvd#gmail.com>
#
# This file is released under PSF license by Igor Ghisi.
# To get the original version of this file, visit:
# http://code.activestate.com/      Recipe: 496761
# Thanks a lot for this great code!

"""
   This file contains a class of ordered dict, which
could be reused by other programs.
"""

from UserDict import DictMixin

class ODict(DictMixin):
    """
    Ordered dict.
    """
    
    def __init__(self, data = None):
        self._keys = []
        self._data = {}
        
        if data is not None:
            if hasattr(data, 'items'):
                items = data.items()
            else:
                items = list(data)
            for i in xrange(len(items)):
                length = len(items[i])
                if length != 2:
                    raise ValueError('dictionary update sequence element '
                        '#%d has length %d; 2 is required' % (i, length))
                self._keys.append(items[i][0])
                self._data[items[i][0]] = items[i][1]
        
    def __setitem__(self, key, value):
        if key not in self._data:
            self._keys.append(key)
        self._data[key] = value
        
    def __getitem__(self, key):
        return self._data[key]
    
    def __delitem__(self, key):
        del self._data[key]
        self._keys.remove(key)
        
    def keys(self):
        """
        D.keys() -> list of D's keys
        """
        return self._keys[:]
    
    def copy(self):
        """
        D.copy() -> a shallow copy of D
        """
        copy_dict = ODict()
        copy_dict._data = self._data.copy()
        copy_dict._keys = self._keys[:]
        return copy_dict

