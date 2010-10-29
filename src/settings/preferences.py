"""Programmatic interface to default and user-defined preferences.

See the preferences documentation for more info."""

from __future__ import print_function

import collections
import cPickle as pickle
import os
import tempfile
import threading
from contextlib import contextmanager
from itertools import dropwhile
from os.path import join, pardir, isdir, isfile, dirname
from pprint import pprint

import plat
import settings
from plat import OS, OSX, WINXP, LINUX32, LINUX64
from plat import USER_PREFS_FILE as user_prefs
from util import die

if OS == OSX: import _prefs_osx as _plat_prefs
elif OS == WINXP: import _prefs_winxp as _plat_prefs
elif OS == LINUX32: import _prefs_linux32 as _plat_prefs
elif OS == LINUX64: import _prefs_linux64 as _plat_prefs
else: die('unknown OS: {0}', OS)

# -- Locking primitives ------------------------------------------------------#

def __pref_locked():
    # python closures suck
    lock = [threading.Lock()]
    def pref_locked():
        lock[0].acquire()
        try:
            yield
        except:
            raise
        finally:
            lock[0].release()
    return pref_locked

# Context manager for acquiring the lock, doing something, releasing it
pref_locked = contextmanager(__pref_locked())

def pref_atomic(f):
    def atomic(*args, **kwargs):
        with pref_locked():
            return f(*args, **kwargs)
    return atomic

# -- Thread-safe functions ---------------------------------------------------#

@pref_atomic
def preference(key):
    global _prefs
    return _prefs[key]

@pref_atomic
def preference_with_default(key, default):
    try: return preference(key)
    except: return default

@pref_atomic
def has_preference(key):
    global _prefs
    return key in _prefs

@pref_atomic
def save():
    global _prefs
    _unsafe_save_prefs(user_prefs, _prefs)

@pref_atomic
def set_and_save(preference, value):
    global _prefs
    _prefs[preference] = value
    _unsafe_save_prefs(user_prefs, _prefs)

# -- Global defaults (platform-specific in _plat_prefs) ----------------------#

__DEBUG = False

pcfg = collections.namedtuple('pcfg', 'desc pickle_default')

PREF_CONFIG = \
{'build_dir':
     pcfg(u"Parent build directory.  When a sketch is compiled, " + \
              u"its build directory will be a child of this directory.",
          False),

 'build_dir_delete_on_exit':
     pcfg(u'If true (default), deletes the parent build directory when ' + \
              'the IDE exits.',
          False),

 'editor_emacs_keybindings':
     pcfg(u'If true (default), enables some emacs keybindings in the editor.',
          False),

 'editor_insert_tabs':
     pcfg(u'Whether or not the editor will insert literal TAB characters. ' + \
              u'When disabled, if you press the tab key, ' + \
              u'the editor inserts a number of spaces equal to the value ' + \
              u'of the {editor_tab_width} preference. ' + \
              u'If enabled, pressing the tab key inserts a literal ' + \
              u'tab character.',
          False),

 'editor_tab_indents_line':
     pcfg(u'If enabled (default is disabled), pressing the tab key will ' + \
              u'indent the line, rather than inserting a tab character ' + \
              u'or equivalent number of spaces.',
          False),

 'editor_tab_width':
     pcfg(u'Number of spaces to display for one tab.', True),

 'lib_maple_home':
     pcfg(u"Path to the libmaple source tree to compile against. " + \
              "If missing, default is the version bundled with MapleIDE. " + \
              "MapleIDE and libmaple are released in lockstep to ease " + \
              "debugging, so be aware that versions of libmaple obtained " + \
              "from github are likely to be less stable.",
          False),

 'make_path':
     pcfg(u"Absolute path to the make executable.   " + \
              u"If missing, default is the version bundled with MapleIDE. " + \
              u"Make is a program in the compilation process.  If you're " + \
              u"unfamiliar with Make, this preference is probably best " + \
              u"left alone.",
          False),

 'sketchbook':
     pcfg(u"Directory containing the user's sketches.", True),

 'user_libs':
     pcfg(u"Directory containing the user's libraries.", True),
 }

# Defaults delayed in order to prevent unintended side effects.
_global_defaults = {
    'build_dir': lambda: tempfile.mkdtemp(prefix=u'maple-build'),
    'build_dir_delete_on_exit': lambda: True,
    'editor_emacs_keybindings': lambda: False,
    'editor_insert_tabs': lambda: False,
    'editor_tab_indents_line': lambda: False,
    'editor_tab_width': lambda: 4,
    'lib_maple_home': lambda: join(settings.DEPENDENCIES_DIR, u'libmaple'),
    'make_path': lambda: join(settings.DEPENDENCIES_DIR,
                              plat.OS, u'make', u'bin', u'make'),
    }

# -- Unsafe functions --------------------------------------------------------#

def _unsafe_load_prefs():              # TODO error handling
    # assumes you've got the lock already
    pref_dict = {}

    defaults = _global_defaults.copy()
    defaults.update(_plat_prefs.platform_defaults)

    if not isfile(user_prefs):
        # no user prefs, force all delays
        for p in PREF_CONFIG: pref_dict[p] = defaults[p]()

        # make a new user prefs file, at least the parts we want
        _unsafe_save_prefs(user_prefs, pref_dict)

        if __DEBUG:
            print('pickled prefs:')
            pprint(to_pickle)

    else:
        with open(user_prefs, 'rb') as f_in:
            user_dict = pickle.load(f_in)

        for p in PREF_CONFIG:
            if p in user_dict: pref_dict[p] = user_dict[p]
            else: pref_dict[p] = defaults[p]()

    if __DEBUG:
        print('all prefs:')
        pprint(pref_dict)

    return pref_dict

def _unsafe_save_prefs(path, pref_dict):
    if not isdir(dirname(path)): os.makedirs(dirname(path))

    to_pickle = dict((k,v) for (k,v) in pref_dict.iteritems() \
                         if PREF_CONFIG[k].pickle_default)

    with open(path, 'wb') as f_out:
        pickle.dump(to_pickle, f_out)

# -- Initialization ----------------------------------------------------------#

with pref_locked():
    _prefs = _unsafe_load_prefs()
