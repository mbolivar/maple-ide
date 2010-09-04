"""This is just an abstraction barrier so we can separate all the
wxPython from the model-y, controller-y bits.
"""

class UserInterface(object):
    """Specifies the programmatic interface the GUI must meet in order
    to interact with the non-GUI components.
    """

    # don't use abstract base classes so we can still use python 2.5

    #-------------------------- You implement these --------------------------#

    def show_warning(self, sketch, message):
        raise NotImplementedError()

    def show_error(self, sketch, message):
        raise NotImplementedError()

    def redisplay(self, sketch):
        """Restore the sketch's on-screen state.
        """
        raise NotImplementedError()

    def clear_compiler_window(self, sketch):
        raise NotImplementedError()

    def append_compiler_output(self, sketch, line):
        raise NotImplementedError()

    def set_compiler_status(self, sketch, status):
        raise NotImplementedError()

