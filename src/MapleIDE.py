#!/usr/bin/env python

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

#------------------------------------------------------------------------------

class CPPStyledTextCtrl(wx.stc.StyledTextCtrl):
    """A CPPStyledTextCtrl is a text editor window that knows how to
    highlight C++ code."""

    def __init__(self, parent):
        wx.stc.StyledTextCtrl.__init__(self, parent, id=wx.ID_ANY,
                                       style=wx.NO_BORDER | wx.TE_MULTILINE)

        # !@#$ this was badly documented. best i could find was
        # http://www.yellowbrain.com/stc/index.html
        #
        # in particular:
        # http://www.yellowbrain.com/stc/lexing.html
        # http://www.yellowbrain.com/stc/styling.html
        self.SetLexer(wx.stc.STC_LEX_CPP)

        # specify the c++ keywords.  it's crap that i have to, given
        # that THEY ALREADY WROTE A LEXER
        cpp_keywords = \
            ["and", "and_eq", "asm", "auto", "bitand", "bitor", "bool",
             "break", "case", "catch", "char", "class", "compl", "const",
             "const_cast", "continue", "default", "delete", "do", "double",
             "dynamic_cast", "else", "enum", "explicit", "export", "extern",
             "false", "float", "for", "friend", "goto", "if", "inline", "int",
             "long", "mutable", "namespace", "new", "not", "not_eq",
             "operator", "or", "or_eq", "private", "protected", "public",
             "register", "reinterpret_cast", "return", "short", "signed",
             "sizeof", "static", "static_cast", "struct", "switch", "template",
             "this", "throw", "true", "try", "typedef", "typeid", "typename",
             "union", "unsigned", "using", "virtual", "void", "volatile",
             "wchar_t", "while", "xor", "xor_eq"]
        self.SetKeyWords(0, ' '.join(cpp_keywords))

        # specify how to style various kinds of syntax elements.  it
        # is also total crap that the default is "they're all the same".
        # http://wiki.wxpython.org/AnotherTutorial#Standard_Colour_Database
        gray = wx.Color(126, 126, 126)
        darkish_blue = wx.Color(0, 102, 153)
        orange = wx.Color(204, 102, 0)
        goldenrod = wx.Color(205, 155, 29)
        self.StyleClearAll()    # cargo cult code
        self.StyleSetForeground(wx.stc.STC_C_WORD, orange) # !@#$ KEYWORD
        self.StyleSetForeground(wx.stc.STC_C_CHARACTER, darkish_blue)
        self.StyleSetForeground(wx.stc.STC_C_STRING, darkish_blue)
        self.StyleSetForeground(wx.stc.STC_C_STRINGEOL, darkish_blue)
        self.StyleSetForeground(wx.stc.STC_C_COMMENT, gray)
        self.StyleSetForeground(wx.stc.STC_C_COMMENTDOC, gray)
        self.StyleSetForeground(wx.stc.STC_C_COMMENTDOCKEYWORD, gray)
        self.StyleSetForeground(wx.stc.STC_C_COMMENTDOCKEYWORDERROR, gray)
        self.StyleSetForeground(wx.stc.STC_C_COMMENTLINE, gray)
        self.StyleSetForeground(wx.stc.STC_C_COMMENTLINEDOC, gray)
        self.StyleSetForeground(wx.stc.STC_C_IDENTIFIER, goldenrod)
        self.StyleSetForeground(wx.stc.STC_C_NUMBER, 'BLUE')
        self.StyleSetForeground(wx.stc.STC_C_PREPROCESSOR, 'FIREBRICK')
        # dunno wtf these are, but they exist, just so you know:
        # wx.stc.STC_C_[REGEX,DEFAULT,GLOBALCLASS,UUID,VERBATIM,WORD2]

        # set properties
        # TODO [mbolivar] enable folding? i hate it, but others seem not to
        self.SetProperty("styling.within.preprocessor", "0")
        self.SetProperty("fold.comment", "0")
        self.SetProperty("fold.preprocessor", "0")
        self.SetProperty("fold.compact", "0")

        # tabs and spaces.  these values are set mostly according to
        # my personal religion [mbolivar], except that tab doesn't do
        # indentation, it just causes a tab to be inserted; IDE users
        # might get surprised/frustrated by tab = indent-line
        self.SetUseTabs(False)
        self.SetTabWidth(4)
        self.SetTabIndents(False)

#------------------------------------------------------------------------------

class SketchFrame(wx.Frame):
    """wx.Frame for showing a sketch: verify/etc. buttons, tabbed view
    of the files in the sketch, sketch status, window for compiler
    output, and last compile's exit status.

    I.e., it's a repeat of the usual Wiring/Arduino interface.
    """

    def __init__(self, parent=None, id=wx.ID_ANY, title="Maple IDE",
                 pos=(50,50), size=(640,480), style=wx.DEFAULT_FRAME_STYLE,
                 name="Maple IDE"):
        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)

        # this thing totally takes the pain out of panel layout
        self.__mgr = wx.aui.AuiManager(self)

        # toolbar
        self.toolbar = self.CreateToolBar()
        button_pieces = resources.desprite_bitmap(settings.TOOLBAR_BUTTONS, 7)
        verify, stop, new_sk, open_sk, save_sk, upload, serial = button_pieces
        self._add_to_toolbar(verify, self.OnVerify)
        self._add_to_toolbar(stop, self.OnStop)
        self._add_to_toolbar(new_sk, self.OnNewSketch)
        self._add_to_toolbar(open_sk, self.OnOpenSketch)
        self._add_to_toolbar(save_sk, self.OnSaveSketch)
        self._add_to_toolbar(upload, self.OnUpload)
        self._add_to_toolbar(serial, self.OnSerialMonitor)
        self.toolbar.Realize()

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

        # TODO this is just for demoing/debugging
        self._demo_mockup()

    def _demo_mockup(self):
        for n in range(1, 5):
            page = self.MakeNewTab("this is tab %d" % n)
            page.SetText('\n'.join(['#define HELLO "WORLD"',
                                    '',
                                    'int x = 3; // a comment!',
                                    "char b = 'c';",
                                    'char *s = "string!"',
                                    ''
                                    '/** another comment! */',
                                    'int main(char **argv, int argc) {'
                                    '    return 0;'
                                    '}']))
        self.SetCaptionText('Compilation b0rked!')
        self.comp.AppendText('file.c:23:you messed up!')
        self.SetStatusText('look, i set the status text!')

    def MakeNewTab(self, name):
        page = CPPStyledTextCtrl(self.nb)
        self.nb.AddPage(page, name)
        return page

    def _add_to_toolbar(self, bitmap, click_handler):
        tool_id = wx.NewId()
        self.toolbar.SetToolBitmapSize(bitmap.GetSize())
        self.toolbar.AddTool(tool_id, bitmap)
        self.Bind(wx.EVT_TOOL, click_handler, id=tool_id)
        return tool_id

    def SetCaptionText(self, text):
        # just stashing comp_info in __init__ won't work; i think
        # AuiManager makes a fresh AuiPaneInfo for any window you give it
        info = self.__mgr.GetPane(self.comp)
        info.Caption(text)
        self.__mgr.Update()

    #------------------------- Frame event handlers ---------------------------

    def OnClose(self, evt):
        self.__mgr.UnInit()
        self.Destroy()

    #--------------------------- Toolbar handlers ----------------------------

    def OnVerify(self, evt):
        print 'verify not done yet!'   # TODO

    def OnStop(self, evt):
        print 'not done!'       # TODO

    def OnNewSketch(self, evt):
        print 'not done!'       # TODO

    def OnOpenSketch(self, evt):
        print 'not done!'       # TODO

    def OnSaveSketch(self, evt):
        print 'not done!'       # TODO

    def OnUpload(self, evt):
        print 'not done!'       # TODO

    def OnSerialMonitor(self, evt):
        print 'not done!'       # TODO

#------------------------------------------------------------------------------

assertMode = wx.PYAPP_ASSERT_EXCEPTION

#------------------------------------------------------------------------------

class MapleIDEApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def __init__(self, name):
        self.name = name
        wx.App.__init__(self, redirect=False)


    def OnInit(self):
        self.SetAssertMode(assertMode)
        self.Init()  # InspectionMixin

        ## Menu bar
        self.menu_bar = self._make_menu_bar()

        ## Initial sketch frame
        self.frame = self._make_sketch_frame()
        self.SetTopWindow(self.frame)
        return True

    def _make_menu_bar(self):
        menu_bar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        item = file_menu.Append(-1, "&New\tCtrl-N", "New Sketch")
        self.Bind(wx.EVT_MENU, self.OnNewSketch, item)
        item = file_menu.Append(-1, "&Open...\tCtrl-O",
                                 "Open an existing sketch")
        self.Bind(wx.EVT_MENU, self.OnOpenSketch, item)
        item = file_menu.Append(-1, "SKETCHBOOK SUBMENU") # TODO
        self.Bind(wx.EVT_MENU, self.OnSketchBookSubmenu, item)
        item = file_menu.Append(-1, "EXAMPLES SUBMENU") # TODO
        self.Bind(wx.EVT_MENU, self.OnExamplesSubmenu, item)
        item = file_menu.Append(-1, "Close\tCTRL-W", "Close this sketch")
        self.Bind(wx.EVT_MENU, self.OnClose, item)
        item = file_menu.Append(-1, "&Save\tCTRL-S", "Save open file")
        self.Bind(wx.EVT_MENU, self.OnSave, item)
        item = file_menu.Append(-1, "S&ave As...\tSHIFT-CTRL-S",
                                 "Save to a new sketch")
        self.Bind(wx.EVT_MENU, self.OnSaveAs, item)
        item = file_menu.Append(-1, "&Upload to I/O Board\tCTRL-U")
        self.Bind(wx.EVT_MENU, self.OnUpload, item)
        file_menu.AppendSeparator()
        item = file_menu.Append(-1, "Page Setup\tSHIFT-CTRL-P")
        self.Bind(wx.EVT_MENU, self.OnPageSetup, item)
        item = file_menu.Append(-1, "Print\tCTRL-P")
        self.Bind(wx.EVT_MENU, self.OnPrint, item)
        # TODO take this stuff out
        file_menu.AppendSeparator()
        item = file_menu.Append(-1, "E&xit\tCtrl-Q", "Exit demo")
        self.Bind(wx.EVT_MENU, self.OnExitApp, item)
        item = file_menu.Append(-1, "&Widget Inspector\tF6",
                            "Show the wxPython Widget Inspection Tool")
        self.Bind(wx.EVT_MENU, self.OnWidgetInspector, item)

        menu_bar.Append(file_menu, "&File")

        # Edit menu
        edit_menu = wx.Menu()
        item = edit_menu.Append(-1, "&Undo\tCTRL-Z")
        self.Bind(wx.EVT_MENU, self.OnUndo, item)
        item = edit_menu.Append(-1, "&Redo\tCTRL-Y")
        self.Bind(wx.EVT_MENU, self.OnRedo, item)
        edit_menu.AppendSeparator()
        item = edit_menu.Append(-1, "&Cut\tCTRL-X")
        self.Bind(wx.EVT_MENU, self.OnCut, item)
        item = edit_menu.Append(-1, "C&opy\tCTRL-C")
        self.Bind(wx.EVT_MENU, self.OnCopy, item)
        item = edit_menu.Append(-1, "Copy for &Forum\tSHIFT-CTRL-C")
        self.Bind(wx.EVT_MENU, self.OnCopyForForum, item)
        item = edit_menu.Append(-1, "Copy as &HTML\tALT-CTRL-C")
        self.Bind(wx.EVT_MENU, self.OnCopyAsHTML, item)
        item = edit_menu.Append(-1, "P&aste\tCTRL-V")
        self.Bind(wx.EVT_MENU, self.OnPaste, item)
        item = edit_menu.Append(-1, "Select &All\tCTRL-A")
        self.Bind(wx.EVT_MENU, self.OnSelectAll, item)
        edit_menu.AppendSeparator()
        item = edit_menu.Append(-1, "Co&mment/Uncomment\tCTRL-/")
        self.Bind(wx.EVT_MENU, self.OnCommentUncomment, item)
        item = edit_menu.Append(-1, "&Increase Indent\tCTRL-]")
        self.Bind(wx.EVT_MENU, self.OnIncreaseIndent, item)
        item = edit_menu.Append(-1, "&Decrease Indent\tCTRL-[")
        self.Bind(wx.EVT_MENU, self.OnDecreaseIndent, item)
        edit_menu.AppendSeparator()
        item = edit_menu.Append(-1, "&Find...\tCTRL-F")
        self.Bind(wx.EVT_MENU, self.OnFind, item)
        item = edit_menu.Append(-1, "Find &Next\tCTRL-G")
        self.Bind(wx.EVT_MENU, self.OnFindNext, item)

        menu_bar.Append(edit_menu, "&Edit")

        # Sketch menu
        sketch_menu = wx.Menu()
        item = sketch_menu.Append(-1, "&Verify / Compile\tCTRL-R")
        self.Bind(wx.EVT_MENU, self.OnVerify, item)
        item = sketch_menu.Append(-1, "&Stop")
        self.Bind(wx.EVT_MENU, self.OnStop, item)
        sketch_menu.AppendSeparator()
        item = sketch_menu.Append(-1, "&Show Sketch Folder\tCTRL-K")
        self.Bind(wx.EVT_MENU, self.OnShowSketchFolder, item)
        item = sketch_menu.Append(-1, "IMPORT LIBRARY SUBMENU") # TODO
        self.Bind(wx.EVT_MENU, self.OnImportLibrary, item)
        item = sketch_menu.Append(-1, "&Add File...")
        self.Bind(wx.EVT_MENU, self.OnAddFile, item)

        menu_bar.Append(sketch_menu, "&Sketch")

        # Tools menu
        tools_menu = wx.Menu()
        item = tools_menu.Append(-1, "&Auto Format\tCTRL-T")
        self.Bind(wx.EVT_MENU, self.OnAutoFormat, item)
        item = tools_menu.Append(-1, "A&rchive Sketch")
        self.Bind(wx.EVT_MENU, self.OnArchiveSketch, item)
        item = tools_menu.Append(-1, "&Fix Encoding and Reload")
        self.Bind(wx.EVT_MENU, self.OnFixEncodingAndReload, item)
        tools_menu.AppendSeparator()
        item = tools_menu.Append(-1, "Serial Monitor\tSHIFT-CTRL-M")
        self.Bind(wx.EVT_MENU, self.OnSerialMonitor, item)
        tools_menu.AppendSeparator()
        item = tools_menu.Append(-1, "BOARDS SUBMENU") # TODO
        self.Bind(wx.EVT_MENU, self.OnBoardsSubmenu, item)
        item = tools_menu.Append(-1, "SERIAL PORT SUBMENU") # TODO
        self.Bind(wx.EVT_MENU, self.OnSerialPortSubmenu, item)
        tools_menu.AppendSeparator()
        item = tools_menu.Append(-1, "BURN BOOTLOADER SUBMENU")
        self.Bind(wx.EVT_MENU, self.OnBurnBootloader, item)

        menu_bar.Append(tools_menu, "&Tools")

        # Help menu
        help_menu = wx.Menu()
        item = help_menu.Append(-1, "Getting Started")
        self.Bind(wx.EVT_MENU, self.OnGettingStarted, item)
        item = help_menu.Append(-1, "Development Environment")
        self.Bind(wx.EVT_MENU, self.OnDevelopmentEnvironment, item)
        item = help_menu.Append(-1, "Troubleshooting")
        self.Bind(wx.EVT_MENU, self.OnTroubleshooting, item)
        item = help_menu.Append(-1, "Language Reference")
        self.Bind(wx.EVT_MENU, self.OnLanguageReference, item)
        item = help_menu.Append(-1, "Visit Arduino.cc")
        self.Bind(wx.EVT_MENU, self.OnVisitArduino, item)
        item = help_menu.Append(-1, "Visit LeafLabs.com")
        self.Bind(wx.EVT_MENU, self.OnVisitLeafLabs, item)

        menu_bar.Append(help_menu, "&Help")

        return menu_bar

    def _make_sketch_frame(self):
        frame = SketchFrame()
        frame.SetMenuBar(self.menu_bar)
        frame.Show(True)

        return frame

    #-------------------------------------------------------------------------#

    def NotImplementedPopup(self):
        popup = wx.MessageDialog(None, "Sorry!", "Not implemented yet", wx.OK)
        popup.ShowModal()
        popup.Destroy()

    #----------------------- File Menu event handlers ------------------------#

    def OnNewSketch(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnOpenSketch(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnSketchBookSubmenu(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnExamplesSubmenu(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnClose(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnSave(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnSaveAs(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnUpload(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnPageSetup(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnPrint(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnExitApp(self, evt):
        self.frame.Close(True)  # TODO remove

    def OnWidgetInspector(self, evt): # TODO remove
        wx.lib.inspection.InspectionTool().Show()


    #----------------------- Edit Menu event handlers ------------------------#

    def OnUndo(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnRedo(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnCut(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnCopy(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnCopyForForum(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnCopyAsHTML(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnPaste(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnSelectAll(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnCommentUncomment(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnIncreaseIndent(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnDecreaseIndent(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnFind(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnFindNext(self, evt):
        # TODO
        self.NotImplementedPopup()

    #---------------------- Sketch Menu event handlers -----------------------#

    def OnVerify(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnStop(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnShowSketchFolder(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnImportLibrary(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnAddFile(self, evt):
        # TODO
        self.NotImplementedPopup()

    #---------------------- Sketch Menu event handlers -----------------------#

    def OnAutoFormat(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnArchiveSketch(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnFixEncodingAndReload(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnSerialMonitor(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnBoardsSubmenu(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnSerialPortSubmenu(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnBurnBootloader(self, evt):
        # TODO
        self.NotImplementedPopup()

    #----------------------- Help menu event handlers ------------------------#

    def OnGettingStarted(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnDevelopmentEnvironment(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnTroubleshooting(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnLanguageReference(self, evt):
        # TODO
        self.NotImplementedPopup()

    def OnVisitArduino(self, evt):
        webbrowser.open_new_tab('http://arduino.cc')

    def OnVisitLeafLabs(self, evt):
        webbrowser.open_new_tab('http://leaflabs.com')

#----------------------------------------------------------------------------

def main(argv):
    name, ext  = os.path.splitext(argv[1])

    app = MapleIDEApp(name)
    app.MainLoop()

if __name__ == '__main__':
  main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
