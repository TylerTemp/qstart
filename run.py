import sys
import os
import imp

if (hasattr(sys, "frozen") or  # new py2exe
        hasattr(sys, "importers") or  # old py2exe
        imp.is_frozen("__main__")):
    ROOTDIR = os.path.dirname(sys.executable)
else:
    ROOTDIR = os.path.dirname(sys.argv[0])

sys.path.insert(0, ROOTDIR)
from lib.tool import bashlog
logger = bashlog.stdoutlogger(None, bashlog.DEBUG, True)
from lib.qstart import main
sys.path.pop(0)


if __name__ == '__main__':
    main()
