import wx
import wx.stc

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

