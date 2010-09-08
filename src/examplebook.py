"""Utility functions for dealing with existing sketches in the
examples Leaf provides.
"""

import os
from os import listdir
from os.path import isdir, join

import settings

EXAMPLES = settings.EXAMPLEBOOK_DIR

def _abs(c): return join(EXAMPLES, c)

def categories():
    return [d for d in os.listdir(EXAMPLES) if isdir(_abs(d))]

def categories_abs():
    return [_abs(c) for c in example_categories()]

def category_get_abs(c):
    return _abs(c)

def category_examples(c):
    return listdir(_abs(c))

def example_get_abs(category, example):
    return _abs(join(category, example))

