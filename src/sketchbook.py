"""Utility functions for dealing with existing sketches in the user's
sketchbook.
"""

import datetime
import os
import os.path
import string
from datetime import datetime
from os import listdir
from os.path import isdir, join

import settings
from settings import SKETCH_EXN as EXN
from settings.preferences import preference as P
from Sketch import Sketch

_unsaved_sketches = set()

def _abs(d): return join(P('sketchbook'), d)

def mark_saved(sketch):
    if sketch not in _unsaved_sketches:
        # already marked, or it was never unsaved
        return
    _unsaved_sketches.remove(sketch)

def is_sketchdir(d):
    return bool([x for x in listdir(d) if x.endswith(EXN)])

def sketch_dirs():
    return [d for d in map(_abs, listdir(P('sketchbook'))) if \
                isdir(d) and d != P('user_libs') and is_sketchdir(d)]

def sketch_dirs_abs():
    return [_abs(d) for d in sketch_dirs()]

def sketch_dir_get_abs(sketch_dir):
    return _abs(sketch_dir)

def most_recent_sketch_dir():   # preferences go stale
    skds = sketch_dirs_abs()
    def latest_mtime(skd):      # TODO something faster?
        mtimes = [os.path.getmtime(join(skd, f)) for f in listdir(skd)]
        if mtimes: return max(mtimes)
        else: return -1
    return max(skds, key=latest_mtime)

def most_recent_sketch_file():
    """Returns the path to the main file of the most recently edited
    sketch.  If there are no sketches, returns None."""
    d = most_recent_sketch_dir()
    return sketch_main_file(d) if d else None

def sketch_source_files(d):
    return [x for x in listdir(d) if x.endswith(EXN)]

def _fresh_name(fmt, existing_names):
    name = u''
    for c in string.ascii_lowercase:
        name = fmt.format(fresh=c)
        if name not in existing_names: break
    else:
        # we ran out of letters, just use numbers
        i = 1
        while True:
            name = fmt.format(fresh=u'-' + unicode(i))
            if name not in existing_sketches: break
            i += 1
    return name

def fresh_sketch(ui):          # FIXME races with self and file system
    """nobody else should be touching the sketchbook directory!"""
    global _unsaved_sketches

    date_str = unicode(datetime.now().strftime('%b%d').lower())
    fmt = u'sketch_{0}{{fresh}}'.format(date_str)
    existing_sketches = set(sketch_dirs() + list(_unsaved_sketches))

    name = _fresh_name(fmt, existing_sketches)
    _unsaved_sketches.add(name)
    main_file = os.path.join(_abs(name), name + EXN)

    return Sketch(ui, main_file, unsaved=True)

def fresh_sketch_archive(sketch): # FIXME races like fresh_sketch
    date_str = unicode(datetime.now().strftime('%y%m%d'))
    name_fmt = u'{n}_{d}{{fresh}}.zip'.format(n=sketch.name, d=date_str)
    existing = set(a for a in listdir(P('sketchbook')) if \
                       a.endswith(u'.zip'))

    return _fresh_name(name_fmt, existing)

def sketch_main_file(sketch_dir):
    """Given a nonempty sketch directory, try to return the absolute
    path to the main file in the sketch.  Returns some file in any
    case."""
    fs = [x for x in listdir(sketch_dir) if x.endswith(EXN)]
    if not fs: return None

    # shortcut: any file with the same name as the sketch directory is
    # a winner
    sketch_name = os.path.basename(sketch_dir)
    for f in fs:
        if f == sketch_name + EXN: return join(sketch_dir, f)

    # ok, that didn't work; try to find a file with a setup method
    # FIXME [HACK] this is pretty lame
    for f in fs:
        with open(os.path.join(sketch_dir,f),'r') as f_in:
            if u'setup' in f_in.read(): return join(sketch_dir, f)

    # oh well, give _something_ back
    return join(sketch_dir, fs[0])
