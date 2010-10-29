from pprint import pprint

import wx
from wx.stc import *

from settings.preferences import preference

# the best primer on StyledTextCtrl i could find (it's old but good):
#
# http://www.yellowbrain.com/stc/index.html

class CPPStyledTextCtrl(StyledTextCtrl):
    """A CPPStyledTextCtrl is a text editor window that knows how to
    highlight C++ code."""

    def __init__(self, parent):
        StyledTextCtrl.__init__(self, parent, id=wx.ID_ANY,
                                       style=wx.NO_BORDER | wx.TE_MULTILINE)

        self.SetLexer(STC_LEX_CPP)

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
        self.StyleSetForeground(STC_C_WORD, orange) # !@#$ KEYWORD
        self.StyleSetForeground(STC_C_CHARACTER, darkish_blue)
        self.StyleSetForeground(STC_C_STRING, darkish_blue)
        self.StyleSetForeground(STC_C_STRINGEOL, darkish_blue)
        self.StyleSetForeground(STC_C_COMMENT, gray)
        self.StyleSetForeground(STC_C_COMMENTDOC, gray)
        self.StyleSetForeground(STC_C_COMMENTDOCKEYWORD, gray)
        self.StyleSetForeground(STC_C_COMMENTDOCKEYWORDERROR, gray)
        self.StyleSetForeground(STC_C_COMMENTLINE, gray)
        self.StyleSetForeground(STC_C_COMMENTLINEDOC, gray)
        self.StyleSetForeground(STC_C_IDENTIFIER, 'BLACK')
        self.StyleSetForeground(STC_C_NUMBER, 'BLUE')
        self.StyleSetForeground(STC_C_PREPROCESSOR, 'FIREBRICK')
        # dunno wtf these are, but they exist, just so you know:
        # STC_C_[REGEX,DEFAULT,GLOBALCLASS,UUID,VERBATIM,WORD2]

        # set properties
        # TODO [mbolivar] enable folding? i hate it, but others seem not to
        self.SetProperty("styling.within.preprocessor", "0")
        self.SetProperty("fold.comment", "0")
        self.SetProperty("fold.preprocessor", "0")
        self.SetProperty("fold.compact", "0")

        self.SetUseTabs(preference('editor_insert_tabs'))
        self.SetTabWidth(preference('editor_tab_width'))
        self.SetTabIndents(preference('editor_tab_indents_line'))

        self._set_keybindings()

    #------------------------------ Keybindings ------------------------------#

    def _set_keybindings(self):
        if preference('editor_emacs_keybindings'):
            self._enable_emacs_keybindings()

    def _enable_emacs_keybindings(self):
        self.CmdKeyAssign(ord('P'), STC_SCMOD_CTRL, STC_CMD_LINEUP)
        self.CmdKeyAssign(ord('N'), STC_SCMOD_CTRL, STC_CMD_LINEDOWN)

        self.CmdKeyAssign(ord('A'), STC_SCMOD_CTRL, STC_CMD_HOME)
        self.CmdKeyAssign(ord('E'), STC_SCMOD_CTRL, STC_CMD_LINEEND)
        self.CmdKeyAssign(ord('B'), STC_SCMOD_CTRL, STC_CMD_CHARLEFT)
        self.CmdKeyAssign(ord('F'), STC_SCMOD_CTRL, STC_CMD_CHARRIGHT)

        self.CmdKeyAssign(ord('B'), STC_SCMOD_ALT, STC_CMD_WORDLEFT)
        self.CmdKeyAssign(ord('F'), STC_SCMOD_ALT, STC_CMD_WORDRIGHT)

        self.CmdKeyAssign(STC_KEY_BACK, STC_SCMOD_ALT, STC_CMD_DELWORDLEFT)


    #-------------------------------------------------------------------------#

    def _lfp(self, p):          # convenience
        return self.LineFromPosition(p)

    def GetCurrentLine(self):
        return self._lfp(self.GetCurrentPos())

    def GenSelectedLineNumbers(self):
        """Returns a generator of all of the currently selected line
        numbers, in order.  If there is no selection, the generator
        will just yield the line containing the current position."""
        si, sf = self.GetSelection()
        return xrange(self._lfp(si), self._lfp(sf) + 1)

    def GenSelectedLines(self):
        """Like `GenSelectedLineNumbers', except it returns the lines
        themselves, newline-terminated."""
        return (self.GetLine(l) for l in self.GenSelectedLineNumbers())

    def DecreaseIndent(self):
        for l in self.GenSelectedLineNumbers():
            i = self.GetLineIndentation(l)
            self.SetLineIndentation(l, max(i - PRIMARY_OFFSET, 0))

    def IncreaseIndent(self):
        for l in self.GenSelectedLineNumbers():
            i = self.GetLineIndentation(l)
            self.SetLineIndentation(l, i + PRIMARY_OFFSET)

    def _select_whole_lines(self):
        # increase the current selection to extend from the beginning
        # of the line it starts on, to the end of the line it finishes
        # at ***UNLESS*** the selection ends at the _beginning_ of a
        # line.  in this case, move the end back one character.
        si, sf = self.GetSelection()
        li, lf = self._lfp(si), self._lfp(sf)

        # reposition si to the beginning of its line
        si = self.PositionFromLine(li)

        # reposition sf
        sf_pfl = self.PositionFromLine(lf)
        if sf == sf_pfl:
            # sf is at the beginning of line lf => place it at the end
            # of line lf - 1, unless yadda yadda corner cases
            sf = self.GetLineEndPosition(max(lf - 1, 0))
        else:
            # sf is at a nonzero column => pull it to the end of lf
            sf = self.GetLineEndPosition(lf)

        # reset the selection.
        self.SetSelection(si, sf)

    def _is_comment_or_blank(self, line):
        return line.lstrip().startswith('//') or line.strip() == '';

    def ToggleCommentUncomment(self):
        old_sel = self.GetSelectedText()
        self._select_whole_lines()

        commenting = False
        lines = []
        for line in self.GenSelectedLines():
            if not self._is_comment_or_blank(line): commenting = True
            lines.append(line)

        # suck it, java
        if commenting: new_lines = ['//' + l for l in lines]
        else: new_lines = [l.replace('//','',1) for l in lines]
        new_lines[-1] = new_lines[-1].rstrip() # or we'll insert an extra \n

        self.ReplaceSelection(''.join(new_lines))
