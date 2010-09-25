"""For parsing GCC output.
"""

import re

#-----------------------------------------------------------------------------#

# These regular expressions match GCC output (adapted from Emacs).
# Supposedly, they catch lines and columns, but empirically, they
# basically only do well at catching the file and the first source
# line of an error.

GCC_REGEXP = r"^(?:[^\W\d](?:[-.]|[^\W])+: ?)?(\d*[^0-9\n](?:[^\n ]| [^-/\n])*?): ?(\d+)(?:([.:])(\d+))?(?:-(\d+)?(?:.(\d+))?)?:(?: *((?:Future|Runtime)?[Ww]arning|W:)| *([Ii]nfo(?:\b|rmationa?l?):|I:|instantiated from:|[Nn]ote:)|\d?(?:[^0-9\n]|$)|\d\d\d)"
GCC_MATCHER = re.compile(GCC_REGEXP, re.UNICODE)
# 1                             # FILE
# (2 . 5)                       # (LINE . END-LINE)
# (4 . 6)                       # (COLUMN . END-COLUMN)
# (7 . 8)                       # (WARNING . INFO)

GCC_INCLUDE_REGEXP = \
    r"^(?:In file included|[ ]{16}) from " + \
    r"(.+):(\d+)(?:(:)|(,))?"
GCC_INCLUDE_MATCHER = re.compile(GCC_INCLUDE_REGEXP, re.UNICODE)
# 1                              # FILE
# 2                              # LINE
# nil                            # column (nil)
# (3 . 4))                       # (WARNING . INFO)

#-----------------------------------------------------------------------------#

def _parse(match, file_idx, line_idx, warn_idx, info_idx):
    file = None
    line = None
    warning = None
    info = None
    message = None
    error = None

    if match:
        groups = match.groups()
        file = groups[file_idx]
        warning = groups[warn_idx]
        if not warning: info = groups[info_idx]
    else:
        return None

    # line or message without file is dumb
    if file:
        line = groups[line_idx]
        span = match.span()
        message = match.string[span[1]:].lstrip(':').lstrip()
        if message.startswith('error: '):
            message = message[7:]
            error = True
            warning = None
            info = None

    return {'file': file, 'line': line,
            'warning': warning, 'info': info, 'error': error,
            'message': message}

def parse_line(line):
    """Returns None or a dict containing the parse output.

    If a dict, contains these keys: 'file', 'line', 'warning', 'info',
    'error', 'message'.

    If file is None, so is line. Otherwise, file is a unicode string,
    and line is either an int or None. At most one of 'warning',
    'info', and 'error' will be non-None, but they might all be None.

    Message is a best-effort."""
    return _parse(GCC_MATCHER.match(line), 0, 1, 6, 7)


def parse_include_line(line):
    """Like parse_gcc_line, except it works on include errors."""
    return _parse(GCC_INCLUDE_MATCHER.match(line), 0, 1, 2, 3)


if __name__ == '__main__':
    from pprint import pprint
    lines = ["foo.c:: message",
             "foo.c: message",
             "foo.c:W: message",
             "foo.c:8: message",
             "../foo.c:8: W: message",
             "/tmp/foo.c:8:warning message",
             "foo/bar.py:8: FutureWarning message",
             "foo.py:8: RuntimeWarning message",
             "foo.c:8:I: message",
             "foo.c:8.23: note: message",
             "foo.c:8.23: info: message",
             "foo.c:8:23:information: message",
             "foo.c:8.23-45: Informational: message",
             "foo.c:8-23: message",
             "foo.c:8-45.3: message",
             "foo.c:8.23-9.1: message",
             "jade:dbcommon.dsl:133:17:E: missing argument for function call",
             "G:/cygwin/dev/build-myproj.xml:54: Compiler Adapter 'javac' can't be found.",
             "file:G:/cygwin/dev/build-myproj.xml:54: Compiler Adapter 'javac' can't be found.",
             "{standard input}:27041: Warning: end of file not at end of a line; newline inserted",
             "main.cpp: In function 'void setup()':",
             "main.cpp:38: error: 'stuff' was not declared in this scope",
             "main.cpp:38: error: expected ';' before 'happens'",
             "make: *** [build/main.o] Error 1",
             "main.cpp:38: error: invalid conversion from 'int' to 'int*'",
             "main.cpp:38: warning: unused variable 'x'",
             "Compilation exited abnormally with code 2 at Mon Oct  4 13:14:22",
             "/Users/mbolivar/hack/leaf/libmaple/libmaple/systick.c:50: error: expected identifier or '(' before 'volatile'",
             "/Users/mbolivar/hack/leaf/libmaple/libmaple/systick.c:53: error: expected identifier or '(' before '}' token",
             "/Users/mbolivar/hack/leaf/libmaple/libmaple/systick.c:55: warning: return makes integer from pointer without a cast"]
    for l in lines:
        print l
        pprint(parse_line(l))
        print '------------'
        print
