"""Class for modelling a sketch, which is just a collection of files
we compile together as a project.

Sketch objects are meant to represent the _desired_ on-disk state of a
set of files.  However, if saves fail etc., a Sketch might get ahead
of the disk.

Sketches know how to compile themselves.  This mixes model/controller
a little bit, but in a way that I'm ok with."""

from __future__ import with_statement

import os.path

from util import temp_dir

#-----------------------------------------------------------------------------#

class MalformedSketchError(RuntimeError):

    def __init__(self, *args, **kwargs):
        RuntimeError.__init__(self, *args, **kwargs)

SKETCH_EXTS = ['pde', 'c', 'cpp', 'h']

#-----------------------------------------------------------------------------#

def make_new_sketch():
    sk = Sketch(None)

class Sketch(object):

    def __init__(self, user_interface, main_file=None):
        """Create a Sketch object.

        main_file = absolute path to main sketch file in top level of
        the sketch's directory.

        user_interface = ui.UserInterface-alike object
        """
        # FIXME need to allow for unsaved sketches -- means a refactor
        # through this and SketchFrame
        if not main_file.endswith('.pde'):
            raise ValueError('invalid main file extension: %s' % main_file)
        self.main_file = main_file
        self.main_name = os.path.basename(main_file)
        self.main_basename = self._strip_ext(self.main_name)
        self.sketch_dir = os.path.dirname(main_file)
        self.sketch_name = os.path.basename(self.sketch_dir)
        self.sources = self.reload_sources() # {basename: code}
        self.ui = user_interface

    def _strip_ext(self, pde_file):
        return pde_file[:-4]

    def _ext(self, path):
        rsplit = path.rsplit('.')
        return rsplit[1] if len(rsplit) > 1 else None

    def redisplay_ui(self):
        self.ui.redisplay()

    def abs_path(self, basename):
        return os.path.join(self.sketch_dir, basename)

    def reset_directory(self, d): # weird if d == '/', but whatever
        self.sketch_dir = d.rstrip(os.path.sep)
        self.sketch_name = os.path.basename(self.sketch_dir)

    def compile(self, build_dir):
        """Assumes the sketch is synced with the hard disk."""
        self.ensure_existence() # ok, arduino, we'll check a little, too

        # FINISH

        self.report_size(binary_path)
        return binary_path

    def save(self, message_on_error=True):
        failed_saves = []
        for basename, code in self.sources.iteritems():
            path = os.path.join(self.sketch_dir, basename)
            try:
                with open(path, 'w') as f:
                    f.write(code)
            except:
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

    def reload_sources(self):
        self.num_files = 0

        sources = {}
        main_found = False
        for f in os.listdir(self.sketch_dir):
            abs_f = self.abs_path(f)
            if f.startswith('.') or self._ext(f) not in SKETCH_EXTS or \
                    not os.path.isfile(abs_f):
                continue

            if abs_f == self.main_file: main_found = True
            with open(abs_f, 'r') as f_in:
                source = f_in.read()
                sources[f] = source

        if not main_found:
            # TODO better error reporting
            raise MalformedSketchError('missing main file %s from dir %d' % \
                                           (self.main_file, self.sketch_dir))

        return sources

    def source(self, basename):
        return self.sources[basename]

    def replace_source(self, basename, new_code):
        if basename not in self.sources:
            # TODO better error reporting
            raise ValueError('%s not a source' % basename)
        self.sources[basename] = new_code

    def insert_source(self, basename, new_code):
        if basename in self.sources:
            # TODO better error reporting
            raise ValueError('%s already a source' % basename)
        self.sources[basename] = new_code

    def __get_num_sources(self):
        return len(self.sources)
    num_sources = property(fget=__get_num_sources)

    def ensure_existence(self):
        if os.path.exists(self.sketch_dir): return True
        self.ui.show_ok_warning(["Sketch disappeared",
                                 "Your sketch folder has disappeared.\n" + \
                                     "Maple IDE will attempt to restore " + \
                                     "your source code, but other data " + \
                                     "will be lost."])
        try:
            os.mkdirs(self.sketch_dir)
            for basename in self.sources:
                with open(self.abs_path(basename), 'w') as f_out:
                    f_out.write(self.sources[basename])
        except:
            self.ui.show_ok_warning(["Sketch restoration failed",
                                     "Could not restore all of your " + \
                                         "source code.  Some changes " + \
                                         "may be lost.  You should attempt " +\
                                         "to save your work elsewhere."])


#-----------------------------------------------------------------------------#

