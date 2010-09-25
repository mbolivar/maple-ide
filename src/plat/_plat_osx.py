"""OS X platform-specific preferences."""

import subprocess
from os.path import join

def _appscript(script):
    lines = subprocess.Popen(['osascript', '-e', script],
                             stdout=subprocess.PIPE).stdout.readlines()
    return unicode(lines[0].rstrip('\n'))

def _appscript_path(f_spec):
    return _appscript('POSIX path of (path to {0})'.format(f_spec))

documents = _appscript_path('documents folder')
app_data = _appscript_path('application support folder from user domain')
user_prefs = join(app_data, 'MapleIDE', 'preferences.pickle')
