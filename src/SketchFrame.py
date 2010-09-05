"""SketchFrame is our view class for a Sketch and the assorted
operations you can perform on it.  It's the usual Arduino-style
editing window with toolbar, tabbed notebook of all the .pde files in
the sketch, and compilation output area.
"""

import os
import sys
import webbrowser
from pprint import pprint

import wx
import wx.aui
import wx.lib.inspection
import wx.lib.mixins.inspection
import wx.stc

import resources
import settings
import examplebook as EB
import sketchbook as SB
from ui import UserInterface
from wx_util import not_implemented_popup, warning_popup, error_popup
from CPPStyledTextCtrl import CPPStyledTextCtrl
from Sketch import Sketch

STATUS_SUCCESS = 0              # FIXME this needs a better place

#-----------------------------------------------------------------------------#

def make_sketch_frame(main_file, parent=None, id=wx.ID_ANY, pos=(50, 50),
                      size=(640, 480), style=wx.DEFAULT_FRAME_STYLE):
    basename = os.path.basename(main_file)
    frame = SketchFrame(parent=parent, id=id, title="Maple IDE | "+basename,
                        pos=pos, size=size, style=style)
    sketch = Sketch(frame, main_file)
    frame.SetSketch(sketch)
    return frame

#----------------------------------------------------------------------------#-

class SketchFrame(wx.Frame, UserInterface):
    """wx.Frame for showing a sketch: verify/etc. buttons, tabbed view
    of the files in the sketch, sketch status, window for compiler
    output, and last compile's exit status.

    I.e., it's mostly a rehash of the usual Wiring/Arduino interface.
    """

    def __init__(self, parent=None, id=wx.ID_ANY, title="Maple IDE",
                 pos=(50,50), size=(640,480), style=wx.DEFAULT_FRAME_STYLE,
                 name="Maple IDE"):
        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)

        self._pages = {}        # {basename: CPPStyledTextCtrl}

        # this thing totally takes the pain out of panel layout
        self.__mgr = wx.aui.AuiManager(self)

        # menu bar
        self.menu_bar = self._make_menu_bar()
        self.SetMenuBar(self.menu_bar)

        # toolbar
        self._make_toolbar()

        # status bar
        self.CreateStatusBar()

        # tabbed view of current sketch
        self.nb = wx.aui.AuiNotebook(self)

        # compiler output
        self.comp = wx.TextCtrl(self, -1, '', wx.DefaultPosition,
                                wx.Size(200, 150),
                                wx.NO_BORDER | wx.TE_MULTILINE)
        comp_info = wx.aui.AuiPaneInfo()
        comp_info.Bottom()
        comp_info.CaptionVisible(True)
        comp_info.CloseButton(False)
        comp_info.Floatable(False)

        # add the panes to the manager
        self.__mgr.AddPane(self.nb, wx.CENTER)
        self.__mgr.AddPane(self.comp, info=comp_info)
        self.__mgr.Update()

        # set frame close handler
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    #--------------------------- Menu bar creation ---------------------------#

    def _make_menu_bar(self):
        menu_bar = wx.MenuBar()

        ## convenience functions so we don't have to repeat ourselves x1e6
        def bind_handler(menu, text, handler):
            item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, handler, item)
        def make_bind(menu):
            return lambda txt, handler: bind_handler(menu, txt, handler)

        ## File menu
        file_menu = wx.Menu()
        bind = make_bind(file_menu)

        # sketchbook submenu/bindings
        sketchbook_menu = wx.Menu()
        sketches = SB.sketch_dirs()
        open_sketch = lambda s: \
            lambda evt: self.OpenSketchNewFrame(SB.sketch_dir_get_abs(s))
        sketchbook_bind = make_bind(sketchbook_menu)
        for s in sketches: sketchbook_bind(s, open_sketch(s))
        # examples submenu/bindings
        examples_menu = wx.Menu()
        categories = EB.categories()
        open_example = lambda c,e: \
            lambda evt: self.OpenSketchNewFrame(EB.example_get_abs(c,e))
        for c in categories:
            cat_menu = wx.Menu()
            cat_bind = make_bind(cat_menu)
            for e in EB.category_examples(c):
                cat_bind(e, open_example(c, e))
            examples_menu.AppendMenu(-1, c, cat_menu)
        # file menu/bindings
        bind("&New\tCtrl-N", self.OnNewSketch)
        bind("&Open...\tCtrl-O", self.OnOpenSketch)
        file_menu.AppendMenu(-1, "Sketchbook", sketchbook_menu)
        file_menu.AppendMenu(-1, "Examples", examples_menu)
        bind("Close\tCTRL-W", self.OnClose)
        bind("&Save\tCTRL-S", self.OnSave)
        bind("S&ave As...\tSHIFT-CTRL-S", self.OnSaveAs)
        bind("&Upload to I/O Board\tCTRL-U", self.OnUpload)
        file_menu.AppendSeparator()
        bind("&Page Setup\tSHIFT-CTRL-P", self.OnPageSetup)
        bind("Print\tCTRL-P", self.OnPrint)

        menu_bar.Append(file_menu, "&File")

        ## Edit menu
        edit_menu = wx.Menu()
        bind = make_bind(edit_menu)

        bind("&Undo\tCTRL-Z", self.OnUndo)
        bind("&Redo\tCTRL-Y", self.OnRedo)
        edit_menu.AppendSeparator()
        bind("&Cut\tCtrl-X", self.OnCut)
        bind("C&opy\tCTRL-C", self.OnCopy)
        bind("Copy for &Forum\tSHIFT-CTRL-C", self.OnCopyForForum)
        bind("Copy as &HTML\tALT-CTRL-C", self.OnCopyAsHTML)
        bind("P&aste\tCTRL-V", self.OnPaste)
        bind("Select &All\tCTRL-A", self.OnSelectAll)
        edit_menu.AppendSeparator()
        bind("Co&mment/Uncomment\tCTRL-/", self.OnCommentUncomment)
        bind("&Increase Indent\tCTRL-]", self.OnIncreaseIndent)
        bind("&Decrease Indent\tCTRL-[", self.OnDecreaseIndent)
        edit_menu.AppendSeparator()
        bind("&Find\tCTRL-F", self.OnFind)
        bind("Find &Next\tCTRL-G", self.OnFindNext)

        menu_bar.Append(edit_menu, "&Edit")

        ## Sketch menu
        sketch_menu = wx.Menu()
        bind = make_bind(sketch_menu)

        bind("&Verify / Compile\tCTRL-R", self.OnVerify)
        bind("&Stop", self.OnStop)
        sketch_menu.AppendSeparator()
        bind("S&how Sketch Folder\tCTRL-K", self.OnShowSketchFolder)
        bind("IMPORT LIBRARY SUBMENU", self.OnImportLibrary)
        bind("&Add File...", self.OnAddFile)

        menu_bar.Append(sketch_menu, "&Sketch")

        ## Tools menu
        tools_menu = wx.Menu()
        bind = make_bind(tools_menu)

        bind("&Auto Format\tCTRL-T", self.OnAutoFormat)
        bind("A&rchive Sketch", self.OnArchiveSketch)
        bind("&Fix Encoding and Reload", self.OnFixEncodingAndReload)
        tools_menu.AppendSeparator()
        bind("&Serial Monitor\tSHIFT-CTRL-M", self.OnSerialMonitor)
        tools_menu.AppendSeparator()
        bind("BOARDS SUBMENU", self.OnBoardsSubmenu) # TODO
        bind("SERIAL PORT SUBMENU", self.OnSerialPortSubmenu) # TODO
        tools_menu.AppendSeparator()
        bind("BURN_BOOTLOADER", self.OnBurnBootloader) # TODO

        menu_bar.Append(tools_menu, "&Tools")

        ## Help menu
        help_menu = wx.Menu()
        bind = make_bind(help_menu)

        bind("Getting Started", self.OnGettingStarted)
        bind("Development Environment", self.OnDevelopmentEnvironment)
        bind("Troubleshooting", self.OnTroubleshooting)
        bind("Language Reference", self.OnLanguageReference)
        bind("Visit Arduino.cc", self.OnVisitArduino)
        bind("Visit LeafLabs.com", self.OnVisitLeafLabs)

        menu_bar.Append(help_menu, "&Help")

        return menu_bar

    #---------------------------- Toolbar creation ---------------------------#

    def _make_toolbar(self):
        self.toolbar = self.CreateToolBar()
        button_pieces = resources.desprite_bitmap(settings.TOOLBAR_BUTTONS, 7)
        verify, stop, new_sk, open_sk, save_sk, upload, serial = button_pieces
        self._add_to_toolbar(verify, self.OnVerify)
        self._add_to_toolbar(stop, self.OnStop)
        self._add_to_toolbar(new_sk, self.OnNewSketchToolbar)
        self._add_to_toolbar(open_sk, self.OnOpenSketchToolbar)
        self._add_to_toolbar(save_sk, self.OnSave)
        self._add_to_toolbar(upload, self.OnUpload)
        self._add_to_toolbar(serial, self.OnSerialMonitor)
        self.toolbar.Realize()

    def _add_to_toolbar(self, bitmap, click_handler):
        tool_id = wx.NewId()
        self.toolbar.SetToolBitmapSize(bitmap.GetSize())
        self.toolbar.AddTool(tool_id, bitmap)
        self.Bind(wx.EVT_TOOL, click_handler, id=tool_id)
        return tool_id

    #-------------------------------------------------------------------------#

    def MakeNewTab(self, name):
        page = CPPStyledTextCtrl(self.nb)
        print 'adding new name:',name
        self.nb.AddPage(page, name)
        return page

    def SetCaptionText(self, text):
        # just stashing comp_info in __init__ won't work; i think
        # AuiManager makes a fresh AuiPaneInfo for any window you give it
        info = self.__mgr.GetPane(self.comp)
        info.Caption(text)
        self.__mgr.Update()

    def SetSketch(self, sketch):
        self.sketch = sketch

        # clear the compiler output
        self.clear_compiler_window()

        # delete existing pages in the notebook
        for i in xrange(self.nb.GetPageCount()):
            self.nb.DeletePage(i)

        # populate the notebook with pages from the sketch
        for basename, code in self.sketch.sources.iteritems():
            page = self.MakeNewTab(basename)
            page.SetText(code)
            self._pages[basename] = page

        self.RedisplayUI()

    def RedisplayUI(self):
        """Must be called AFTER the sketch is set!
        """
        if self.sketch is None:
            raise RuntimeError("no sketch set")

        page_count = self.nb.GetPageCount()
        for basename, source in self.sketch.sources.iteritems():
            page = self._pages[basename]
            page_idx = self.nb.GetPageIndex(page)
            if page_idx == wx.NOT_FOUND:
                print 'ERROR unknown:',basename # TODO better error reporting
                page = self.MakeNewTab(basename)

            page_count -= 1
            page.SetText(source)
        if page_count != 0:
            print 'ERROR: page count is weird:',page_count

    def OpenSketchNewFrame(self, sketch_file):
        """Requires an absolute path to either a .pde file, or a
        directory containing at least one .pde file.
        """
        if os.path.isdir(sketch_file):
            # just pick any pde file in the directory and use that; we
            # open all of them when we start the new frame
            fs = [x for x in os.listdir(sketch_file) if x.endswith('.pde')]
            if not fs:
                error_popup("Empty Sketch Directory",
                            "The directory:\n\t%s\ncontains no .pde files.")
                return
            sketch_file = os.path.join(sketch_file, fs[0])

        x,y = self.GetScreenPositionTuple()
        # FIXME [mbolivar] smarter decision making on where to put the
        # new frame -- maybe making it a child of this frame will DTRT?
        new_frame = make_sketch_frame(sketch_file, pos=(x+20,y+20))
        new_frame.Show(True)

    #----------------------- File Menu event handlers ------------------------#

    def OnNewSketch(self, evt):
        # TODO
        not_implemented_popup()

    def OnOpenSketch(self, evt):
        dialog = wx.FileDialog(None, "Open a Maple Sketch...",
                               defaultDir=settings.SKETCHBOOK_PATH,
                               wildcard="*.pde",
                               style=wx.FD_FILE_MUST_EXIST | wx.FD_OPEN)
        dialog.ShowModal()
        path = dialog.GetPath()
        dialog.Destroy()
        if path == "": return   # user hit cancel
        self.OpenSketchNewFrame(path)

    def OnSketchBookSubmenu(self, evt):
        # TODO
        not_implemented_popup()

    def OnExamplesSubmenu(self, evt):
        # TODO
        not_implemented_popup()

    def OnClose(self, evt):
        # TODO prompt to save etc.
        self.__mgr.UnInit()
        self.Destroy()

    def OnSave(self, evt):
        # TODO
        not_implemented_popup()

    def OnSaveAs(self, evt):
        # TODO
        not_implemented_popup()

    def OnUpload(self, evt):
        # TODO
        not_implemented_popup()

    def OnPageSetup(self, evt):
        # TODO
        not_implemented_popup()

    def OnPrint(self, evt):
        # TODO
        not_implemented_popup()

    #----------------------- Edit Menu event handlers ------------------------#

    def OnUndo(self, evt):
        # TODO
        not_implemented_popup()

    def OnRedo(self, evt):
        # TODO
        not_implemented_popup()

    def OnCut(self, evt):
        # TODO
        not_implemented_popup()

    def OnCopy(self, evt):
        # TODO
        not_implemented_popup()

    def OnCopyForForum(self, evt):
        # TODO
        not_implemented_popup()

    def OnCopyAsHTML(self, evt):
        # TODO
        not_implemented_popup()

    def OnPaste(self, evt):
        # TODO
        not_implemented_popup()

    def OnSelectAll(self, evt):
        # TODO
        not_implemented_popup()

    def OnCommentUncomment(self, evt):
        # TODO
        not_implemented_popup()

    def OnIncreaseIndent(self, evt):
        # TODO
        not_implemented_popup()

    def OnDecreaseIndent(self, evt):
        # TODO
        not_implemented_popup()

    def OnFind(self, evt):
        # TODO
        not_implemented_popup()

    def OnFindNext(self, evt):
        # TODO
        not_implemented_popup()

    #---------------------- Sketch Menu event handlers -----------------------#

    def OnVerify(self, evt):
        # TODO
        not_implemented_popup()

    def OnStop(self, evt):
        # TODO
        not_implemented_popup()

    def OnShowSketchFolder(self, evt):
        # TODO
        not_implemented_popup()

    def OnImportLibrary(self, evt):
        # TODO
        not_implemented_popup()

    def OnAddFile(self, evt):
        # TODO
        not_implemented_popup()

    #----------------------- Tools Menu event handlers -----------------------#

    def OnAutoFormat(self, evt):
        # TODO
        not_implemented_popup()

    def OnArchiveSketch(self, evt):
        # TODO
        not_implemented_popup()

    def OnFixEncodingAndReload(self, evt):
        # TODO
        not_implemented_popup()

    def OnSerialMonitor(self, evt):
        # TODO
        not_implemented_popup()

    def OnBoardsSubmenu(self, evt):
        # TODO
        not_implemented_popup()

    def OnSerialPortSubmenu(self, evt):
        # TODO
        not_implemented_popup()

    def OnBurnBootloader(self, evt):
        # TODO
        not_implemented_popup()

    #----------------------- Help menu event handlers ------------------------#

    def _open_url(self, url):
        # unspecified behavior when it's a file:// url, but it seems to work
        webbrowser.open_new_tab(url)

    def OnGettingStarted(self, evt):
        self._open_url('file://' + resources.reference('quickstart.html'))

    def OnDevelopmentEnvironment(self, evt):
        self._open_url('file://' + resources.reference('index.html'))

    def OnTroubleshooting(self, evt):
        self._open_url('file://' + resources.reference('troubleshooting.html'))

    def OnLanguageReference(self, evt):
        self._open_url('file://' + resources.reference('language.html'))

    def OnVisitArduino(self, evt):
        self._open_url('http://arduino.cc')

    def OnVisitLeafLabs(self, evt):
        self._open_url('http://leaflabs.com')

    #------------------------ Toolbar event handlers -------------------------#

    ## mostly don't need to be written.  all but these taken care of
    ## by existing menu bar handlers.

    def OnNewSketchToolbar(self, evt):
        not_implemented_popup()

    def OnOpenSketchToolbar(self, evt):
        not_implemented_popup()

    #------------------------ UserInterface methods --------------------------#

    def show_warning(self, message):
        warning_popup(message[0], message[1])

    def show_error(self, message):
        error_popup(message[0], message[1])

    def redisplay(self):
        self.RedisplayUI()

    def clear_compiler_window(self):
        self.SetStatusText("")
        self.comp.Clear()

    def append_compiler_output(self, line):
        # TODO parse the line to see if it looks like a compiler error
        # and make a clickable link if so
        self.comp.AppendText(line)

    def set_compiler_status(self, status):
        self.SetStatusText("Compiler exit status: %d" % status)
        if status == STATUS_SUCCESS:
            self.SetCaptionText('Done compiling.')
        else:
            self.SetCaptionText('Compilation was unsuccessful.')

#-----------------------------------------------------------------------------#
