from os.path import join

import plat

platform_defaults = {
    'sketchbook': lambda: join(plat.DOCUMENTS, 'MapleIDE'),
    'user_libs': lambda: join(plat.DOCUMENTS, 'MapleIDE', 'libraries')
    }
