#!/usr/bin/env python

"""Executable entry point to the IDE.
"""

import os
import sys

import wx

import sketchbook
from wx_util import not_implemented_popup, warning_popup, error_popup
from SketchFrame import SketchFrame, make_sketch_frame

assert_mode = wx.PYAPP_ASSERT_EXCEPTION

#-----------------------------------------------------------------------------#

class MapleIDEApp(wx.App):
    def __init__(self, name):
        self.name = name
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        self.SetAssertMode(assert_mode)

        ## Initial sketch frame -- this whole thing is shitty and
        ## needs to be fixed
        sketch_d = sketchbook.most_recent_sketch_dir()
        sketch_pde = sketchbook.sketch_pdes(sketch_d)[0] # FIXME
        sketch_pde = os.path.join(sketch_d, sketch_pde)
        frame = make_sketch_frame(sketch_pde)
        frame.Show(True)
        self.SetTopWindow(frame)

        return True

#-----------------------------------------------------------------------------#

def main(argv):
    name, ext  = os.path.splitext(argv[1])

    app = MapleIDEApp(name)
    app.MainLoop()

if __name__ == '__main__':
    main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
