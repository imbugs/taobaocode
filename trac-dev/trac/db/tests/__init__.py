import unittest

from trac.db.tests import api
from trac.db.tests import postgres_test

from trac.db.tests.functional import functionalSuite

def suite():

    suite = unittest.TestSuite()
    suite.addTest(api.suite())
    suite.addTest(postgres_test.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

