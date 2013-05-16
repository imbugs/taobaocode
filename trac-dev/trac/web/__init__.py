# With mod_python we'll have to delay importing trac.web.api until
# modpython_frontend.handler() has been called since the
# PYTHON_EGG_CACHE variable is set from there
#
# TODO: Remove this once the Genshi zip_safe issue has been resolved.
import os
from pkg_resources import get_distribution
if not os.path.isdir(get_distribution('genshi').location):
    try:
        import mod_python.apache
        import sys
        if 'trac.web.modpython_frontend' in sys.modules:
            from trac.web.api import *
    except ImportError:
        from trac.web.api import *
else:
    from trac.web.api import *
