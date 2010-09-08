"""Global settings file.
"""

import os.path
import tempfile

# FIXME this is just stubbed out real quick

# The extension we ouse for our sketches
SKETCH_EXN = '.pde'

# System settings
MAKE_PATH = '/usr/bin/make'
SKETCHBOOK_PATH = os.path.expanduser('~/Documents/MapleIDE')
EXAMPLEBOOK_PATH = '/Applications/MapleIDE.app/Contents/Resources' + \
                                                         '/Java/examples'
SKETCHBOOK_LIB_PATH = os.path.expanduser('~/Documents/MapleIDE/libraries')

# Directory containing libmaple and wirish.
# TODO? allow os.environ to override? probably only as a preference
LIB_MAPLE_HOME = '/Users/mbolivar/hack/leaf/libmaple'

# Build directory parent: all of the sketch-level build directories
# are contained in this top-level one.  Just to be safe, the app nukes
# this directory within a finally: upon exit from the main loop
BUILD_DIR = tempfile.mkdtemp(prefix='maple-build')

# Resources (GUI images, reference docs, etc.)
TOOLBAR_BUTTONS = 'buttons.png'
RESOURCE_DIR = os.path.abspath('../resources')
REFERENCE_DIR = os.path.join(RESOURCE_DIR, 'reference')
