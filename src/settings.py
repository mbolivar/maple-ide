"""Global settings file.
"""

import os.path

# FIXME this is just stubbed out real quick

# System settings
MAKE_PATH = '/usr/bin/make'
SKETCHBOOK_PATH = os.path.expanduser('~/Documents/MapleIDE')
EXAMPLEBOOK_PATH = '/Applications/MapleIDE.app/Contents/Resources' + \
                                                         '/Java/examples'
SKETCHBOOK_LIB_PATH = os.path.expanduser('~/Documents/MapleIDE/libraries')

# Resources
TOOLBAR_BUTTONS = 'buttons.png'
RESOURCE_DIR = os.path.abspath('../resources')
REFERENCE_DIR = os.path.join(RESOURCE_DIR, 'reference')