# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.

import unittest

from trac.web.tests import api, auth, cgi_frontend, chrome, href, session, \
                           wikisyntax

try:
    import neo_cgi
    from trac.web.tests import clearsilver
except ImportError:
    clearsilver = None

def suite():
    suite = unittest.TestSuite()
    suite.addTest(api.suite())
    suite.addTest(auth.suite())
    suite.addTest(cgi_frontend.suite())
    suite.addTest(chrome.suite())
    if clearsilver:
        suite.addTest(clearsilver.suite())
    suite.addTest(href.suite())
    suite.addTest(session.suite())
    suite.addTest(wikisyntax.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
