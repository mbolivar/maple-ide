import shutil
import tempfile
from contextlib import contextmanager

@contextmanager
def temp_dir():
    """Context manager for performing an action using a temporary
    directory:

    with temp_dir() as d:
        ... do something with directory named d ...
    # from this point on, d is not on the system
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix='maple-build')
        yield temp_dir
    except:
        raise
    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    import os.path
    try:
        with temp_dir() as d:
            print 'dir is:',d
            print 'now you see it:',os.path.exists(d)
            raise ValueError()
    except:
        print "now you don't:",os.path.exists(d)
    else:
        print 'but this will not happen'
