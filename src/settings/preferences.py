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
    global _prefs
    try: return _prefs[key]
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
def set_and_save(pref_dict):
    global _prefs
    global _watchers
    delta = {}
    for pref, val in pref_dict.iteritems():
        if val != _prefs[pref]:
            _prefs[pref] = val
            delta[pref] = val
    if delta:
        _unsafe_save_prefs(user_prefs, _prefs)
        for w in _watchers:
            if hasattr(w, 'preferences_changed'):
                w.preferences_changed(delta)
            else:
                w(delta)
    else:
        print('no delta')

@pref_atomic
def register_change_watcher(watcher):
    """Register a change listener on the user preferences.

    This can be an object with a callable 'preferences_changed'
    attribute, or a callable.  When user preferences get changed
    through the use of this module, either the
    watcher.preferences_changed gets called, or, if that doesn't
    exist, watcher itself is called, with argument a dictionary from
    the changed preferences to their new values.

    Try not to use this; do so only if you're interacting with some
    third party code that needs to keep current."""
    global _watchers
    _watchers.append(watcher)

# -- Global defaults (platform-specific in _plat_prefs) ----------------------#

__DEBUG = False

# General info for a preferences.
#
# desc: (Short) string description
# help: Longer description
# group: Preference group ('Compilation', 'General', etc.)
# type: Kind of preference, (currently) one of: ['path', 'dir', 'bool', 'int']
pcfg = collections.namedtuple('pcfg', 'desc help group type pickle_default')

PREF_CONFIG = \
{'build_dir':
     pcfg(u'Parent build directory',
          u'When a sketch is compiled, its build directory will be a ' + \
              u'child of this directory.',
          'Compilation', 'dir', False),

 'build_dir_delete_on_exit':
     pcfg(u'Delete parent build directory on exit',
          u'If true (default), deletes the parent build directory when ' + \
              'the IDE exits.',
          'General', 'bool', False),

 'editor_emacs_keybindings':
     pcfg(u'Emacs keybindings',
          u'If true (default is false), enables some Emacs-style ' + \
              u'keybindings in the editor.',
          'Editor', 'bool', False),

 'editor_insert_tabs':
     pcfg(u'Allow tabs',
          u'Whether or not the editor will insert literal TAB characters. ' + \
              u'When disabled, if you press the tab key, ' + \
              u'the editor inserts a number of spaces equal to the value ' + \
              u'of the Tab Width preference. ' + \
              u'If enabled, pressing the tab key inserts a literal ' + \
              u'tab character.',
          'Editor', 'bool', False),

 'editor_tab_indents_line':
     pcfg(u'Tab indents line',
          u'If enabled (default is disabled), pressing the tab key will ' + \
              u'indent the line, rather than inserting a tab character ' + \
              u'or equivalent number of spaces.',
          'Editor', 'bool', False),

 'editor_tab_width':
     pcfg(u'Tab width', u'Number of spaces to display for one tab.',
          'Editor', 'int', True),

 'lib_maple_home':
     pcfg(u'libmaple home',
          u"Path to the libmaple source tree to compile against. " + \
              "Default is the version bundled with MapleIDE. " + \
              "MapleIDE and libmaple are released in lockstep to ease " + \
              "debugging, so be aware that versions of libmaple obtained " + \
              "from github are likely to be less stable.",
          'Compilation', 'dir', False),

 'make_path':
     pcfg(u'Path to make',
          u"Absolute path to the make executable. " + \
              u"Default is the version bundled with MapleIDE. " + \
              u"Make is a program used during compilation.  If you're " + \
              u"unfamiliar with it, the default is probably best.",
          'Compilation', 'path', False),

 'sketchbook':
     pcfg(u'Sketchbook', u"Directory containing your sketches.",
          'General', 'dir', True),

 'user_libs':
     pcfg(u'Libraries', u"Directory containing your extra libraries.",
          'General', 'dir', True),
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

# change listeners; they get notified when a preference changes
_watchers = []
