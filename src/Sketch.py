"""Class for modelling a sketch, which is just a collection of files
we compile together as a project.

Sketch objects are meant to represent the _desired_ on-disk state of a
set of files.  However, if saves fail etc., a Sketch might get ahead
of the disk.

Sketches know how to compile themselves.  This mixes model/controller
a little bit, but in a way that I'm ok with."""

from __future__ import with_statement

import os.path
import re
import shutil
import subprocess
import tempfile
from subprocess import PIPE, STDOUT

import settings
from settings import SKETCH_EXN as EXN
from util import temp_dir

#-----------------------------------------------------------------------------#

class MalformedSketchError(RuntimeError):

    def __init__(self, *args, **kwargs):
        RuntimeError.__init__(self, *args, **kwargs)

# FIXME decide if we want to support real files in sketch folders
SKETCH_EXTS = [EXN[1:], 'c', 'cpp', 'h']

#-----------------------------------------------------------------------------#

class Sketch(object):

    def __init__(self, user_interface, main_file, unsaved=False):
        """Create a Sketch object.

        main_file: absolute path to main sketch file in top level of
        the sketch's directory.

        user_interface: ui.UserInterface-alike object

        unsaved: set this to True if the sketch doesn't have any files
        on disk yet
        """
        if not main_file.endswith(EXN):
            raise ValueError('invalid main file extension: %s' % main_file)
        self.main_file = main_file
        self.main_basename = os.path.basename(main_file)
        self.dir = os.path.dirname(main_file)
        self.name = os.path.basename(self.dir)
        self.sources = self._reload_sources(unsaved) # {basename: Code}
        self.ui = user_interface
        self.build_dir = tempfile.mkdtemp(dir=settings.BUILD_DIR)
        self.compiling = False  # currently compiling?
        self.no_dir = unsaved

    def _strip_ext(self, sketch_file):
        return sketch_file[:-len(EXN)]

    def _ext(self, path):
        rsplit = path.rsplit('.')
        return rsplit[1] if len(rsplit) > 1 else None

    def redisplay_ui(self):
        self.ui.redisplay()

    def abs_path(self, basename):
        return os.path.join(self.dir, basename)

    def reset_directory(self, d, create=False):
        path = path.rstrip(os.path.sep) # NB '/' ==> '' haha oops

        if create and not os.path.isdir(path):
            try:
                os.makedirs(path)
            except:
                err = ("Could not save to folder '%s', please choose " + \
                           "another folder") % os.path.basename(path)
                self.ui.show_error("Save failed", err)
                return

        self.dir = d.rstrip(os.path.sep)
        self.name = os.path.basename(self.dir)

    def upload(self): # assumes build dir is all set up nice
        # FIXME gotta respect MCU, BOARD, etc.
        self.ui.clear_subprocess_window()
        make = settings.MAKE_PATH
        lmaple = settings.LIB_MAPLE_HOME
        child = subprocess.Popen([make, 'SRCROOT=%s' % lmaple, 'install'],
                                 stdout=PIPE, stderr=STDOUT,
                                 cwd=self.build_dir)
        out_err = child.stdout
        status = child.poll()
        while status is None:
            line = self.prettify_uploader_line(out_err.readline())
            self.ui.append_subprocess_output(line)
            status = child.poll()
        # FIXME maybe need to pull out the rest of the lines?
        self.ui.set_status(status, 'upload')

    def prettify_uploader_line(self, line): # TODO
        return line

    def cleanup(self):
        shutil.rmtree(self.build_dir)

    def stop_compiling(self, FIXME_ignore=False): # TODO
        if FIXME_ignore: return
        self.ui.show_error("Not implemented yet", "Sorry!")

    def compile(self):
        """Assumes the sketch is synced with the hard disk."""
        self.ensure_existence() # ok, arduino, we'll check a little, too

        if self.compiling: self.stop_compiling(FIXME_ignore=True)

        # make isn't always so smart about what needs replacing, so do
        # the equivalent of 'make clean' by nuking the build directory.
        # (don't actually run make clean, because that would be slower)
        shutil.rmtree(self.build_dir)
        self.build_dir = tempfile.mkdtemp(dir=settings.BUILD_DIR)

        self.compiling=True

        try:
            # generate all the c++, compute offsets, and put it all into
            # the build directory
            self.preprocess()

            # set up the ui
            self.ui.clear_subprocess_window()

            # do the compilation, reporting errors, status updates, etc.
            # via the self.ui callback methods
            self.run_make()
        finally:
            self.compiling = False

    def preprocess(self): # FIXME
        # for now, assume the sketch files are valid C++ files that
        # #include each other as appropriate
        abs = lambda b: os.path.join(self.dir, b)
        for basename in self.sources:
            strip = self._strip_ext(basename)
            if basename == self.main_basename:
                shutil.copy(abs(basename),
                            os.path.join(self.build_dir, 'main.cpp'))
            else:
                shutil.copy(abs(basename), self.build_dir)

    def run_make(self): # assumes self.build_dir is all set up
        make = settings.MAKE_PATH
        lmaple = settings.LIB_MAPLE_HOME
        if 'Makefile' not in os.listdir(lmaple):
            self.ui.show_error("Bad libmaple directory",
                               "The libmaple directory on your system (%s)" % \
                                   lmaple + ' is missing a Makefile.  ' + \
                                   'Cannot verify sketch.')
            return
        shutil.copy(os.path.join(lmaple,'Makefile'), self.build_dir)
        # FIXME need to incorporate things like FLASH vs. RAM
        child = subprocess.Popen([make, "SRCROOT=%s" % lmaple],
                                 stdout=PIPE, stderr=STDOUT,
                                 cwd=self.build_dir)
        out_err = child.stdout
        status = child.poll()
        # FIXME this will block, so we won't be able to halt
        # compilation until a multithreaded solution is figured out
        while status is None:
            line = self.prettify_compiler_line(out_err.readline())
            self.ui.append_subprocess_output(line)
            status = child.poll()
        # FIXME maybe need to pull out the rest of the lines (run a
        # final out_err.readlines() here) -- some seem to be missing
        # from the subprocess window; not sure
        self.ui.set_status(status, 'compilation')

    def prettify_compiler_line(self, line): # TODO
        return line

    def save(self, message_on_error=True):
        if self.no_dir:
            try:
                os.makedirs(self.dir)
                self.no_dir = False
            except:
                err = 'Could not create directory:\n\t%s\n' % self.dir
                err += 'Please save your sketch in another location.'
                self.ui.show_error('Save Failed', err)
                return False

        failed_saves = []
        for basename, code in self.sources.iteritems():
            path = os.path.join(self.dir, basename)
            try:
                with open(path, 'w') as f:
                    f.write(code.code)
            except Exception as e:
                print "Couldn't save %s. Reason: %s" % (basename, str(e))
                failed_saves.append(basename)

        if failed_saves:
            if message_on_error:
                if len(failed_saves) == 1:
                    err = 'Could not save file ' + failed_saves[0] + '. ' + \
                        'Please save your sketch in another location.'
                else:
                    err = "The following files could not be saved: " + \
                        ', '.join(failed_saves) + \
                        '.  Please save your sketch in another location.'
                self.ui.show_error("Save Failed", err)
            return False
        return True

    def _reload_sources(self, unsaved=False):
        # DOESN'T ACTUALLY MODIFY self.sources

        # Load the sketch files from disk, and pack them into a dict
        # suitable for saving into self.sources.  If `unsaved' is
        # true, assumes the sketch is new and hasn't got any files;
        # just makes empty Code objects.
        self.num_files = 0

        if unsaved:
            return {self.main_basename : Code('')}

        sources = {}
        main_found = False
        for f in os.listdir(self.dir):
            abs_f = self.abs_path(f)
            if f.startswith('.') or self._ext(f) not in SKETCH_EXTS or \
                    not os.path.isfile(abs_f):
                continue

            if abs_f == self.main_file: main_found = True
            with open(abs_f, 'r') as f_in:
                source = f_in.read()
                sources[os.path.basename(f)] = Code(source)

        if not main_found:
            # TODO better error reporting
            raise MalformedSketchError('missing main file %s from dir %d' % \
                                           (self.main_file, self.dir))

        return sources

    def source(self, basename):
        return self.sources[basename].code

    def replace_source(self, basename, new_code):
        if basename not in self.sources:
            # TODO better error reporting
            raise ValueError('%s not a source' % basename)
        self.sources[basename].code = new_code

    def insert_source(self, basename, new_code):
        if basename in self.sources:
            # TODO better error reporting
            raise ValueError('%s already a source' % basename)
        self.sources[basename].code = new_code

    def __get_num_sources(self):
        return len(self.sources)
    num_sources = property(fget=__get_num_sources)

    def ensure_existence(self):
        if os.path.exists(self.dir): return True
        self.ui.show_ok_warning(["Sketch disappeared",
                                 "Your sketch folder has disappeared.\n" + \
                                     "Maple IDE will attempt to restore " + \
                                     "your source code, but other data " + \
                                     "will be lost."])
        self.no_dir = True
        if not self.save():
            self.ui.show_ok_warning(["Sketch restoration failed",
                                     "Could not restore all of your " + \
                                         "source code.  Some changes " + \
                                         "may be lost.  You should attempt " +\
                                         "to save your work elsewhere."])

    def __str__(self):
        codes_str = ['// ----------- FILE: %s ----------\n%s' % \
                         (basename, str(code)) \
                     for basename, code in self.sources.iteritems()]
        return 'Sketch: %s\n\n%s' % (self.main_basename, '\n'.join(codes_str))

#-----------------------------------------------------------------------------#

class Code(object):
    """Source for a sketch file and associated data."""
    # ok, so there's no associated data yet, but there will be once
    # preprocessing works
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return self.code

    def __repr__(self):
        return 'Code("%s")' % self.code
