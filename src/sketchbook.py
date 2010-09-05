"""Utility functions for dealing with existing sketches in the user's
sketchbook.
"""

import datetime
import os
import os.path
import string
from os import listdir
from os.path import isdir, join

import settings

unsaved_sketches = []

SKETCHES = settings.SKETCHBOOK_PATH
LIBS = settings.SKETCHBOOK_LIB_PATH

def _abs(d): return join(SKETCHES, d)

def sketch_dirs():
    return [d for d in listdir(SKETCHES) if isdir(_abs(d)) and _abs(d) != LIBS]

def sketch_dirs_abs():
    return [_abs(d) for d in sketch_dirs()]

def sketch_dir_get_abs(sketch_dir):
    return _abs(sketch_dir)

def most_recent_sketch_dir():   # FIXME this gotta get fixed
    skd = sketch_dirs_abs()
    skd.sort(key=os.path.getmtime, reverse=True)
    return skd[0] if len(skd) > 0 else None

def fresh_sketch_name():
    """nobody else should be touching the sketchbook"""
    base = datetime.datetime.now().strftime('sketch_%b%d').lower()
    sketches = sketch_dirs()    # FIXME
    for c in string.ascii_lowercase:
        name = base + c
        if name not in sketches:
            unsaved_sketches.append(name)
            return name

if __name__ == '__main__':
    print fresh_sketch_name()
