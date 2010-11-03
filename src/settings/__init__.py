"""Umbrella package for anything configurable about the application.

settings is the secret-keeper for the locations of external resources,
dependencies, etc., and manages user preferences."""

import sys
import tempfile
from os.path import abspath, join, pardir

# [better not have messed with sys.path[0]. it's documented that you
#  shouldn't in MapleIDE.]
_app_top_level = abspath(join(sys.path[0], pardir))

# The extension we use for our sketches.  DO NOT SAY .pde ANYWHERE!
# use this instead.  we might want to change our file extension at
# some point.
SKETCH_EXN = u'.pde'

# Resources (GUI images, reference docs, etc.)
RESOURCE_DIR = join(_app_top_level, u'resources')

# Reference documentation for the current IDE's release of libmaple
REF_DOC_DIR = join(RESOURCE_DIR, u'reference')

# External dependencies (make, CodeSourcery tools, etc.)
DEPENDENCIES_DIR = join(_app_top_level, u'deps')

# Examples.  FIXME this feels icky.
EXAMPLEBOOK_DIR = join(RESOURCE_DIR, 'examples')

# IDE version to display
# FIXME this is kind of a dumb place for it
IDE_VERSION = u'0.1.0-alpha-unstable'
