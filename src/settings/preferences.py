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

_DEBUG = False

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
    _unsafe_save_prefs()

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
        if _DEBUG: print('delta:', delta)
        _unsafe_save_prefs()
        for w in _watchers:
            if hasattr(w, 'preferences_changed'):
                w.preferences_changed(delta)
            else:
                w(delta)
    elif _DEBUG:
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

# General info for a preferences.
#
# desc: (Short) string description
#
# help: Longer description
#
# group: Preference group ('Compilation', 'General', etc.)
#
# type: Kind of preference, (currently) one of: ['path', 'dir',
# 'bool', 'int', 'options'].  The last of these ('options') has a
# "values" key in its extra data.
#
# advanced: counts as an advanced preference
#
# data: Extra data associated with the preference.
#
# pickle: whether or not to pickle this preference (FIXME this is dumb
# and exists only for the build directory; the preference should be
# "use my build directory or not", and if so, then etc.  same for "use
# my make")
pcfg = collections.namedtuple('pcfg',
                              ' '.join(['desc', 'help', 'group', 'type',
                                        'advanced', 'pickle', 'data']))

PREF_CONFIG = \
{'build_dir':
     pcfg(u'Parent build directory',
          u'When a sketch is compiled, its build directory will be a ' + \
              u'child of this directory.',
          u'Compilation', 'dir', False, False, {}),

 'build_dir_delete_on_exit':
     pcfg(u'Delete parent build directory on exit',
          u'If enabled, deletes the parent build directory on IDE exit.',
          u'General', 'bool', False, True, {}),

 'editor_emacs_keybindings':
     pcfg(u'Emacs keybindings',
          u'Enable some Emacs-style keybindings in the editor.',
          u'Editor', 'bool', False, True, {}),

 'editor_insert_tabs':
     pcfg(u'Allow tabs',
          u'Whether or not the editor will insert literal TAB characters. '
          u'If disabled, the editor will insert an equivalent number of '
          u'spaces when the TAB key is pressed.',
          u'Editor', 'bool', False, True, {}),

 'editor_tab_indents_line':
     pcfg(u'Tab indents line',
          u'If enabled pressing the tab key will indent the line, rather '
          u'than inserting a tab character or equivalent number of spaces.',
          u'Editor', 'bool', False, True, {}),

 'editor_tab_width':
     pcfg(u'Tab width', u'Number of spaces to display for one tab.',
          u'Editor', 'int', True, True, {}),

 'lib_maple_home':
     pcfg(u'libmaple home',
          u'Path to the libmaple source tree to compile against. '
          u'Default is the version bundled with MapleIDE, which has the '
          u'same version number as the IDE itself.',
          u'Compilation', 'dir', False, True, {}),

 'make_path':
     pcfg(u'Path to make',
          u'Absolute path to the make executable. '
          u'Default is the version bundled with MapleIDE. '
          u'\n\n'
          u"Make is a program used during compilation.  If you're "
          u"unfamiliar with it, the default is probably best.",
          u'Compilation', 'path', False, True, {}),

 'board':
     pcfg(u'Board', u'Default board to compile to.',
          'Compilation', 'options', True, True,
          {'values': [u'Maple', u'Maple Mini', u'Maple Native']}),

 'memory_target':
     pcfg(u'Memory Target',
          u'Default for where the compiled sketch will reside on your board.',
          u'Compilation', 'options', True, True,
          {'values': [u'RAM', u'Flash']}),

 'sketchbook':
     pcfg(u'Sketchbook', u"Directory containing your sketches.",
          u'General', 'dir', True, True, {}),

 'user_libs':
     pcfg(u'Libraries', u"Directory containing your extra libraries.",
          u'General', 'dir', True, True, {}),
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
    'board': lambda: 'Maple',
    'memory_target': lambda: 'Flash'
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
        _unsafe_save_prefs(pref_dict)

        if _DEBUG:
            print('pickled prefs:')
            pprint(to_pickle)

    else:
        with open(user_prefs, 'rb') as f_in:
            user_dict = pickle.load(f_in)

        for p in PREF_CONFIG:
            if p in user_dict: pref_dict[p] = user_dict[p]
            else: pref_dict[p] = defaults[p]()

    if _DEBUG:
        print('all prefs:')
        pprint(pref_dict)

    return pref_dict

def _unsafe_save_prefs(pref_dict=None):
    if pref_dict is None:
        global _prefs
        pref_dict = _prefs
    if not isdir(dirname(user_prefs)): os.makedirs(dirname(user_prefs))

    to_pickle = dict((p, v) for (p, v) in pref_dict.iteritems() \
                         if PREF_CONFIG[p].pickle)

    if _DEBUG:
        print('saving preferences:', to_pickle)

    with open(user_prefs, 'wb') as f_out:
        pickle.dump(to_pickle, f_out)

# -- Initialization ----------------------------------------------------------#

with pref_locked():
    _prefs = _unsafe_load_prefs()

# change listeners; they get notified when a preference changes
_watchers = []
