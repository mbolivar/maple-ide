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
from settings import SKETCH_EXN as EXN
from Sketch import Sketch

_unsaved_sketches = set()

SKETCHES = settings.SKETCHBOOK_PATH
LIBS = settings.SKETCHBOOK_LIB_PATH

def _abs(d): return join(SKETCHES, d)


def mark_saved(sketch):
    if sketch not in _unsaved_sketches:
        # already marked, or it was never unsaved
        return
    _unsaved_sketches.remove(sketch)

def is_sketchdir(d):
    return bool([x for x in listdir(d) if x.endswith(EXN)])

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

def most_recent_sketch_file():
    """Returns the path to the main file of the most recently edited
    sketch.  If there are no sketches, returns None."""
    d = most_recent_sketch_dir()
    return sketch_main_file(d) if d else None

def sketch_source_files(d):
    return [x for x in listdir(d) if x.endswith(EXN)]

def fresh_sketch(ui):
    """nobody else should be touching the sketchbook directory!"""
    global _unsaved_sketches
    base = datetime.datetime.now().strftime('sketch_%b%d').lower()
    existing_sketches = sketch_dirs() + list(_unsaved_sketches)
    name = ''
    for c in string.ascii_lowercase:
        name = base + c
        if name not in existing_sketches: break
    else:
        # we ran out of letters, just use numbers
        i = 1
        while True:
            name = base + str(i)
            if name not in existing_sketches: break
            i += 1

    _unsaved_sketches.add(name)
    main_file = os.path.join(_abs(name), name + EXN)
    return Sketch(ui, main_file, unsaved=True)

def sketch_main_file(sketch_dir):
    """Given a nonempty sketch directory, return the absolute path to
    the main file in the sketch.
    """
    fs = [x for x in os.listdir(sketch_dir) if x.endswith(EXN)]
    if not fs: return None

    # shortcut: any file with the same name as the sketch directory is
    # a winner
    sketch_name = os.path.basename(sketch_dir)
    for f in fs:
        if f == sketch_name + EXN: return join(sketch_dir, f)

    # ok, that didn't work; try to find a file with a setup method
    # HACK this is a pretty lame attempt
    for f in fs:
        with open(os.path.join(sketch_dir,f),'r') as f_in:
            if 'setup' in f_in.read(): return join(sketch_dir, f)

    # oh well, give _something_ back
    return join(sketch_dir, fs[0])
