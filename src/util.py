from __future__ import print_function

import sys
import traceback as tb

def die(message, traceback=None):
    print('Fatal error: {0}'.format(message), file=sys.stderr)
    if traceback is not None:
        print('Error caused by exception:')
        tb.print_tb(traceback)
    sys.exit(1)
