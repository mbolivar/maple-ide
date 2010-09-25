"""For managing resource files (like images).
"""

import os
import os.path

import wx

import settings
from settings import RESOURCE_DIR

colors = {'LEAF_GREEN': (63, 126, 51)}

TOOLBAR_BUTTONS = u'buttons.png'

_bitmap_cache = {}
_image_cache = {}

def get_resource_file(name):
    return os.path.join(RESOURCE_DIR, name)

def get_image(file_name):
    if file_name in _image_cache:
        return _image_cache[file_name]

    image = wx.Image(get_resource_file(file_name))
    _image_cache[file_name] = image
    return image

def get_bitmap(file_name):
    if file_name in _bitmap_cache:
        return _bitmap_cache[file_name]

    bitmap = wx.BitmapFromImage(get_image(file_name))
    _bitmap_cache[file_name] = bitmap
    return bitmap

def desprite_bitmap(file_name, n_pieces):
    """Assumes horizontal spriting."""
    bmap = get_bitmap(file_name)
    width = bmap.GetWidth()
    assert width % n_pieces == 0
    width = width / n_pieces
    height = bmap.GetHeight()
    pieces = []
    for i in xrange(n_pieces):
        x = width * i
        rect = wx.Rect(x, 0, width, height)
        pieces.append(bmap.GetSubBitmap(rect))
    return pieces

def ref_doc(name):
    return os.path.join(settings.REF_DOC_DIR, name)
