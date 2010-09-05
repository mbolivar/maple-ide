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

_unsaved_sketches = set()

SKETCHES = settings.SKETCHBOOK_PATH
LIBS = settings.SKETCHBOOK_LIB_PATH

def _abs(d): return join(SKETCHES, d)

def mark_saved(sketch):         # this whole thing might be stupid
    if sketch not in _unsaved_sketches:
        # already marked, or it was never unsaved
        return
    _unsaved_sketches.remove(sketch)

def is_sketchdir(d):
    return bool([x for x in listdir(d) if x.endswith('.pde')])

def sketch_dirs():
    return [d for d in listdir(SKETCHES) if \
                isdir(_abs(d)) and _abs(d) != LIBS and is_sketchdir(_abs(d))]

def sketch_dirs_abs():
    return [_abs(d) for d in sketch_dirs()]

def sketch_dir_get_abs(sketch_dir):
    return _abs(sketch_dir)

def most_recent_sketch_dir():   # TODO read from preferences instead?
    skd = sketch_dirs_abs()
    skd.sort(key=os.path.getmtime, reverse=True)
    return skd[0] if len(skd) > 0 else None

def sketch_pdes(d):
    return [x for x in listdir(d) if x.endswith('.pde')]

def fresh_sketch_name():
    """nobody else should be touching the sketchbook"""
    base = datetime.datetime.now().strftime('sketch_%b%d').lower()
    existing_sketches = sketch_dirs() + list(unsaved_sketches)
    for c in string.ascii_lowercase:
        name = base + c
        if name not in existing_sketches:
            pass                # FIXME FIXME FIXME

if __name__ == '__main__':
    print fresh_sketch_name()
