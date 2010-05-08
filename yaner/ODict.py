#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Yaner.

# Yaner - GTK+ interface for aria2 download mananger
# Copyright (C) 2010  Iven Day <ivenvd#gmail.com>
#
# This file is released under PSF license by Igor Ghisi.
# To get the original version of this file, visit:
# http://code.activestate.com/recipes/496761-a-more-clean-implementation-for-ordered-dictionary/
# Thanks a lot for this great code!

from UserDict import DictMixin

class ODict(DictMixin):
    """
    Ordered dict.
    """
    
    def __init__(self):
        self._keys = []
        self._data = {}
        
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
        return self._keys[:]
    
    def copy(self):
        copyDict = odict()
        copyDict._data = self._data.copy()
        copyDict._keys = self._keys[:]
        return copyDict

