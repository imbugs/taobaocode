# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009 Edgewall Software
# Copyright (C) 2005-2007 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.

import doctest
import unittest

import trac.web.href


class HrefTestCase(unittest.TestCase):
    """Unit tests for Href URL builder."""
    
    def test_non_empty_base(self):
        """Build URLs with a non-empty base."""
        href = trac.web.href.Href('/base')
        self.assertEqual('/base', href())
        self.assertEqual('/base', href('/'))
        self.assertEqual('/base/sub', href('sub'))
        self.assertEqual('/base/sub', href('/sub/'))
        self.assertEqual('/base/sub/other', href('sub', 'other'))
        self.assertEqual('/base/sub/other', href('sub', None, 'other'))
        self.assertEqual('/base/sub//other', href('sub', '', 'other'))  # ???
        self.assertEqual('/base/with%20special%26chars',
                         href('with special&chars'))
        assert href('page', param='value', other='other value', more=None) in [
            '/base/page?param=value&other=other+value',
            '/base/page?other=other+value&param=value']
        self.assertEqual('/base/page?param=multiple&param=values',
                         href('page', param=['multiple', 'values']))
        
        self.assertEqual('/base/path/to/file/', href + '/path/to/file/')
        self.assertEqual('/base/path/to/file', href + 'path/to/file')
        self.assertEqual('/base', href + '')

    def test_base_with_trailing_slash(self):
        """Build URLs with a base with a trailing slash."""
        href = trac.web.href.Href('/base/')
        self.assertEqual('/base', href())
        self.assertEqual('/base', href('/'))
        self.assertEqual('/base/sub', href('sub'))
        self.assertEqual('/base/sub', href('/sub/'))
        
        self.assertEqual('/base/path/to/file/', href + '/path/to/file/')
        self.assertEqual('/base/path/to/file', href + 'path/to/file')
        self.assertEqual('/base', href + '')
        
    def test_empty_base(self):
        """Build URLs with an empty base."""
        href = trac.web.href.Href('')
        # The two following href calls don't result in a valid local URL.
        # This is relied upon by existing code (see #8153).
        self.assertEqual('', href())
        self.assertEqual('', href('/'))
        
        self.assertEqual('/sub', href('sub'))
        self.assertEqual('/sub', href('/sub/'))
        self.assertEqual('/sub/other', href('sub', 'other'))
        self.assertEqual('/sub/other', href('sub', None, 'other'))
        self.assertEqual('/sub//other', href('sub', '', 'other'))       # ???
        self.assertEqual('/with%20special%26chars',
                         href('with special&chars'))
        assert href('page', param='value', other='other value', more=None) in [
            '/page?param=value&other=other+value',
            '/page?other=other+value&param=value']
        self.assertEqual('/page?param=multiple&param=values',
                         href('page', param=['multiple', 'values']))
        
        self.assertEqual('/path/to/file/', href + '/path/to/file/')
        self.assertEqual('/path/to/file', href + 'path/to/file')
        self.assertEqual('/', href + '')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(trac.web.href))
    suite.addTest(unittest.makeSuite(HrefTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
