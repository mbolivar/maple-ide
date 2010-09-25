from os.path import join

import plat

platform_defaults = {
    'sketchbook': lambda: join(plat.USER_HOME, 'maple-ide'),
    'user_libs': lambda: join(plat.USER_HOME, 'maple-ide', 'libraries')
    }
