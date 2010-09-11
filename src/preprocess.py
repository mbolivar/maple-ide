"""For preprocessing the PDE language into C++"""

def preprocess(sketch_lines):
    """Given the concatenated source of a sketch file (as an
    iterable of lines), compute the header which should be placed
    in front of it.  Gives this back as a mapping which contains
    the following:

    u'header': list of lines to place as a header (imports and
    prototypes, incl. default imports)

    u'main': list of lines to use as main function.

    u'imports': list of imported user libraries"""
    header, imports = _preprocess(sketch_lines)
    return {u'header': header,
            u'imports': imports,
            u'main': _main()}

def _preprocess(sketch_lines):  # TODO does the work
    return [u''], []

def _main():                    # TODO
    return u''
