"""Platform discovery"""

import os as os_module
import platform

from util import die

def _guess_os():
    s = platform.system()
    bits = platform.architecture()[0]
    if s == 'Darwin':
        return OSX
    elif s == 'Linux':
        if bits == '32bit': return LINUX32
        elif bits == '64bit': return LINUX64
        else: die(u"Unrecognized Linux bit information; " + \
                      u"expected '32bit' or '64bit' but got: %s" % bits)
    elif s == 'Windows':
        # tons of people use windows 7, and some of them might figure
        # out what to do, so pretend we're on win32 and let them try.
        # TODO some warning would be good
        return WINXP32

# supported platforms
OSX    = 'osx'
WINXP   = 'winxp'
LINUX32 = 'linux32'
LINUX64 = 'linux64'

# runtime platform
OS = _guess_os()

if OS == OSX:
    import _plat_osx as _plat
elif OS == WINXP:
    import _plat_winxp as _plat
elif OS == LINUX32:
    import _plat_linux32 as _plat
elif OS == LINUX64:
    import _plat_linux64 as _plat

DOCUMENTS = _plat.documents
APP_DATA = _plat.app_data
USER_PREFS_FILE = _plat.user_prefs
USER_HOME = os_module.path.expanduser('~')
