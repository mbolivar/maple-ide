"""Windows XP platform-specific preferences"""

from os.path import join

import _winreg as winreg

def _environ(var):
    return winreg.ExpandEnvironmentStrings(var)

def _query_value(hkey, sub_key, value_name):
    with winreg.OpenKey(hkey, sub_key) as key:
        return winreg.QueryValueEx(key, value_name)[0]

_docs_sub_key = '\\'.join(['Software', 'Microsoft', 'Windows',
                           'CurrentVersion', 'Explorer', 'Shell Folders'])

documents = _query_value(winreg.HKEY_CURRENT_USER, _docs_sub_key, "Personal")
app_data = _environ(u'%APPDATA%')
user_prefs = join(app_data, 'MapleIDE', 'preferences.pickle')
