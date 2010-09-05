"""This is just an abstraction barrier so we can separate all the
wxPython from the model-y, controller-y bits.
"""

class UserInterface(object):
    """Specifies the programmatic interface the GUI must meet in order
    to interact with the non-GUI components.
    """

    # don't use abstract base classes so we can still use python 2.5?

    def show_warning(self, message, details):
        raise NotImplementedError()

    def show_error(self, message, details):
        raise NotImplementedError()

    def redisplay(self):
        """Restore the sketch's on-screen state.
        """
        raise NotImplementedError()

    def clear_compiler_window(self):
        raise NotImplementedError()

    def append_compiler_output(self, line):
        raise NotImplementedError()

    def set_compiler_status(self, status):
        raise NotImplementedError()

