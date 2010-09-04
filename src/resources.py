"""For managing resource files (like images).
"""

import os
import os.path

import wx

import settings
from settings import RESOURCE_DIR

colors = {'LEAF_GREEN': (63, 126, 51)}

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
    """Assumes horizontal spriting
    """
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

def sketch_dirs():
    jn = lambda d: os.path.join(settings.SKETCHBOOK_PATH, d)
    ds = [jn(d) for d in os.listdir(settings.SKETCHBOOK_PATH)]
    return [d for d in ds if (os.path.isdir(d) and \
                                  d != settings.SKETCHBOOK_LIB_PATH)]

def most_recent_sketch_dir():   # TODO this gotta get fixed
    skd = sketch_dirs()
    skd.sort(key=os.path.getmtime, reverse=True)
    return skd[0] if len(skd) > 0 else None

