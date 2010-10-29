"""Programmatic interface to default and user-defined preferences.

See the preferences documentation for more info."""

from __future__ import print_function

import collections
import cPickle as pickle
import os
import tempfile
from itertools import dropwhile
from os.path import join, pardir, isdir, isfile, dirname
from pprint import pprint

import plat
import settings
from plat import OS, OSX, WINXP, LINUX32, LINUX64
from plat import USER_PREFS_FILE as user_prefs

if OS == OSX: import _prefs_osx as _plat_prefs
elif OS == WINXP: import _prefs_winxp as _plat_prefs
elif OS == LINUX32: import _prefs_linux32 as _plat_prefs
elif OS == LINUX64: import _prefs_linux64 as _plat_prefs

def preference(key):
    global _prefs
    return _prefs[key]

def preference_with_default(key, default):
    try: return preference(key)
    except: return default

def has_preference(key):
    global _prefs
    return key in _prefs

CREATED_USER_PREFS_FILE = False

__DEBUG = False

PCfg = collections.namedtuple('PrefConfig', 'desc pickle_default')

PREF_CONFIG = \
{'build_dir':
     PCfg(u"Parent build directory.  When a sketch is compiled, " + \
              u"its build directory will be a child of this directory.",
          False),

 'build_dir_delete_on_exit':
     PCfg(u'If true (default), deletes the parent build directory when ' + \
              'the IDE exits.',
          False),

 'sketchbook': PCfg(u"Directory containing the user's sketches.", True),

 'user_libs': PCfg(u"Directory containing the user's libraries.", True),

 'lib_maple_home':
     PCfg(u"Path to the libmaple source tree to compile against. " + \
              "If missing, default is the version bundled with MapleIDE. " + \
              "MapleIDE and libmaple are released in lockstep to ease " + \
              "debugging, so be aware that versions of libmaple obtained " + \
              "from github are likely to be less stable.",
          False),

 'make_path':
     PCfg(u"Absolute path to the make executable.   " + \
              u"If missing, default is the version bundled with MapleIDE. " + \
              u"Make is a program in the compilation process.  If you're " + \
              u"unfamiliar with Make, this preference is probably best " + \
              u"left alone.",
          False),

 'editor_emacs_keybindings':
     PCfg(u'If true (default), enables some emacs keybindings in the editor.',
          False)
 }

# Defaults delayed in order to prevent unintended side effects.
_global_defaults = {
    'make_path': lambda: join(settings.DEPENDENCIES_DIR,
                              plat.OS, u'make', u'bin', u'make'),
    'lib_maple_home': lambda: join(settings.DEPENDENCIES_DIR, u'libmaple'),
    'build_dir': lambda: tempfile.mkdtemp(prefix=u'maple-build'),
    'build_dir_delete_on_exit': lambda: True,
    'editor_emacs_keybindings': lambda: True
}

def _load_prefs():              # TODO error handling
    pref_dict = {}

    defaults = _global_defaults.copy()
    defaults.update(_plat_prefs.platform_defaults)

    if not isfile(user_prefs):
        if not isdir(dirname(user_prefs)):
            os.makedirs(dirname(user_prefs))

        # no user prefs, force all delays
        for p in PREF_CONFIG: pref_dict[p] = defaults[p]()

        # make a new user prefs file, at least the parts we want
        to_pickle = dict((k,v) for (k,v) in pref_dict.iteritems() \
                             if PREF_CONFIG[k].pickle_default)

        with open(user_prefs, 'wb') as f_out:
            pickle.dump(to_pickle, f_out)

        if __DEBUG:
            print('pickled prefs:')
            pprint(to_pickle)

        CREATED_USER_PREFS_FILE = True
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

_prefs = _load_prefs()

