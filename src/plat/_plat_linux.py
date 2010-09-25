"""Linux platform-specific preferences that apply to both 32-bit and
64-bit"""

from os.path import expanduser, join

documents = expanduser('~')
app_data = expanduser('~')
user_prefs = join(app_data, '.maple-ide', 'preferences.pickle')
