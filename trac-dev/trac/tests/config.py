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

import os
from StringIO import StringIO
import tempfile
import time
import unittest

from trac.config import *
from trac.test import Configuration


class ConfigurationTestCase(unittest.TestCase):

    if not hasattr(unittest.TestCase, "assertTrue"):
        assertTrue = unittest.TestCase.failUnless   # Python 2.3 compatibility

    def setUp(self):
        self.filename = os.path.join(tempfile.gettempdir(), 'trac-test.ini')
        self._write([])
        self._orig_registry = Option.registry
        Option.registry = {}

    def tearDown(self):
        Option.registry = self._orig_registry
        os.remove(self.filename)

    def _read(self):
        return Configuration(self.filename)

    def _write(self, lines):
        fileobj = open(self.filename, 'w')
        try:
            fileobj.write(('\n'.join(lines + [''])).encode('utf-8'))
        finally:
            fileobj.close()

    def test_default(self):
        config = self._read()
        self.assertEquals('', config.get('a', 'option'))
        self.assertEquals('value', config.get('a', 'option', 'value'))

        class Foo(object):
            option_a = Option('a', 'option', 'value')

        self.assertEquals('value', config.get('a', 'option'))

    def test_default_bool(self):
        config = self._read()
        self.assertEquals(False, config.getbool('a', 'option'))
        self.assertEquals(True, config.getbool('a', 'option', 'yes'))
        self.assertEquals(True, config.getbool('a', 'option', 1))

        class Foo(object):
            option_a = Option('a', 'option', 'true')

        self.assertEquals(True, config.getbool('a', 'option'))

    def test_default_int(self):
        config = self._read()
        self.assertRaises(ConfigurationError, config.getint, 'a', 'option', 'b')
        self.assertEquals(0, config.getint('a', 'option'))
        self.assertEquals(1, config.getint('a', 'option', '1'))
        self.assertEquals(1, config.getint('a', 'option', 1))

        class Foo(object):
            option_a = Option('a', 'option', '2')

        self.assertEquals(2, config.getint('a', 'option'))

    def test_default_path(self):
        config = self._read()
        class Foo(object):
            option_a = PathOption('a', 'opt1', 'file.ini')
            option_b = PathOption('a', 'opt2', '/somewhere/file.ini')
        self.assertEquals('file.ini', config.get('a', 'opt1'))
        self.assertNotEquals('file.ini', config.getpath('a', 'opt1'))
        self.assertTrue(os.path.isabs(config.getpath('a', 'opt1')))
        self.assertEquals('/somewhere/file.ini', os.path.splitdrive(
                config.getpath('a', 'opt2'))[1].replace('\\', '/'))
        self.assertEquals('/none.ini', os.path.splitdrive(
                config.getpath('a', 'opt3', '/none.ini'))[1].replace('\\', '/'))
        self.assertNotEquals('none.ini', config.getpath('a', 'opt3', 'none.ini'))

    def test_read_and_get(self):
        self._write(['[a]', 'option = x'])
        config = self._read()
        self.assertEquals('x', config.get('a', 'option'))
        self.assertEquals('x', config.get('a', 'option', 'y'))
        self.assertEquals('y', config.get('b', 'option2', 'y'))

    def test_read_and_get_unicode(self):
        self._write([u'[ä]', u'öption = x'])
        config = self._read()
        self.assertEquals('x', config.get(u'ä', u'öption'))
        self.assertEquals('x', config.get(u'ä', u'öption', 'y'))
        self.assertEquals('y', config.get('b', u'öption2', 'y'))

    def test_read_and_getbool(self):
        self._write(['[a]', 'option = yes'])
        config = self._read()
        self.assertEquals(True, config.getbool('a', 'option'))
        self.assertEquals(True, config.getbool('a', 'option', False))
        self.assertEquals(False, config.getbool('b', 'option2'))
        self.assertEquals(False, config.getbool('b', 'option2', False))
        self.assertEquals(False, config.getbool('b', 'option2', 'disabled'))

    def test_read_and_getint(self):
        self._write(['[a]', 'option = 42'])
        config = self._read()
        self.assertEquals(42, config.getint('a', 'option'))
        self.assertEquals(42, config.getint('a', 'option', 25))
        self.assertEquals(0, config.getint('b', 'option2'))
        self.assertEquals(25, config.getint('b', 'option2', 25))
        self.assertEquals(25, config.getint('b', 'option2', '25'))

    def test_read_and_getlist(self):
        self._write(['[a]', 'option = foo, bar, baz'])
        config = self._read()
        self.assertEquals(['foo', 'bar', 'baz'],
                          config.getlist('a', 'option'))
        self.assertEquals([],
                          config.getlist('b', 'option2'))
        self.assertEquals(['foo', 'bar', 'baz'],
                    config.getlist('b', 'option2', ['foo', 'bar', 'baz']))
        self.assertEquals(['foo', 'bar', 'baz'],
                    config.getlist('b', 'option2', 'foo, bar, baz'))

    def test_read_and_getlist_sep(self):
        self._write(['[a]', 'option = foo | bar | baz'])
        config = self._read()
        self.assertEquals(['foo', 'bar', 'baz'],
                          config.getlist('a', 'option', sep='|'))

    def test_read_and_getlist_keep_empty(self):
        self._write(['[a]', 'option = ,bar,baz'])
        config = self._read()
        self.assertEquals(['bar', 'baz'], config.getlist('a', 'option'))
        self.assertEquals(['', 'bar', 'baz'],
                          config.getlist('a', 'option', keep_empty=True))

    def test_getpath(self):
        config = self._read()
        config.set('a', 'path_a', '/somewhere/file.txt')
        config.set('a', 'path_b', 'file.txt')
        config.set('a', 'path_c', './file.txt')
        self.assertEquals('/somewhere/file.txt', os.path.splitdrive(
                config.getpath('a', 'path_a'))[1].replace('\\', '/'))
        self.assertNotEquals('file.txt', config.getpath('a', 'path_b'))
        self.assertEquals(config.getpath('a', 'path_b'),
                          config.getpath('a', 'path_c'))

    def test_set_and_save(self):
        config = self._read()
        config.set('b', u'öption0', 'y')
        config.set(u'aä', 'öption0', 'x')
        config.set('aä', 'option2', "Voilà l'été")  # UTF-8
        config.set(u'aä', 'option1', u"Voilà l'été") # unicode
        # Note: the following would depend on the locale.getpreferredencoding()
        # config.set('a', 'option3', "Voil\xe0 l'\xe9t\xe9") # latin-1
        self.assertEquals('x', config.get(u'aä', u'öption0'))
        self.assertEquals(u"Voilà l'été", config.get(u'aä', 'option1'))
        self.assertEquals(u"Voilà l'été", config.get(u'aä', 'option2'))
        config.save()

        configfile = open(self.filename, 'r')
        self.assertEquals(['# -*- coding: utf-8 -*-\n',
                           '\n',
                           '[aä]\n',
                           "option1 = Voilà l'été\n", 
                           "option2 = Voilà l'été\n", 
                           'öption0 = x\n', 
                           # "option3 = VoilÃ  l'Ã©tÃ©\n", 
                           '\n',
                           '[b]\n',
                           'öption0 = y\n', 
                           '\n'],
                          configfile.readlines())
        configfile.close()
        config2 = Configuration(self.filename)
        self.assertEquals('x', config2.get(u'aä', u'öption0'))
        self.assertEquals(u"Voilà l'été", config2.get(u'aä', 'option1'))
        self.assertEquals(u"Voilà l'été", config2.get(u'aä', 'option2'))
        # self.assertEquals(u"Voilà l'été", config2.get('a', 'option3'))

    def test_set_and_save_inherit(self):
        def testcb():
            config = self._read()
            config.set('a', 'option2', "Voilà l'été")  # UTF-8
            config.set('a', 'option1', u"Voilà l'été") # unicode
            self.assertEquals('x', config.get('a', 'option'))
            self.assertEquals(u"Voilà l'été", config.get('a', 'option1'))
            self.assertEquals(u"Voilà l'été", config.get('a', 'option2'))
            config.save()

            configfile = open(self.filename, 'r')
            self.assertEquals(['# -*- coding: utf-8 -*-\n',
                               '\n',
                               '[a]\n',
                               "option1 = Voilà l'été\n", 
                               "option2 = Voilà l'été\n", 
                               '\n',
                               '[inherit]\n',
                               "file = trac-site.ini\n", 
                               '\n'],
                              configfile.readlines())
            configfile.close()
            config2 = Configuration(self.filename)
            self.assertEquals('x', config2.get('a', 'option'))
            self.assertEquals(u"Voilà l'été", config2.get('a', 'option1'))
            self.assertEquals(u"Voilà l'été", config2.get('a', 'option2'))
        self._test_with_inherit(testcb)

    def test_simple_remove(self):
        self._write(['[a]', 'option = x'])
        config = self._read()
        config.get('a', 'option') # populates the cache
        config.set(u'aä', u'öption', u'öne')
        config.remove('a', 'option')
        self.assertEquals('', config.get('a', 'option'))
        config.remove(u'aä', u'öption')
        self.assertEquals('', config.get('aä', 'öption'))
        config.remove('a', 'option2') # shouldn't fail
        config.remove('b', 'option2') # shouldn't fail

    def test_sections(self):
        self._write(['[a]', 'option = x', '[b]', 'option = y'])
        config = self._read()
        self.assertEquals(['a', 'b'], config.sections())
        
        class Foo(object):
            option_c = Option('c', 'option', 'value')
        
        self.assertEquals(['a', 'b', 'c'], config.sections())

    def test_sections_unicode(self):
        self._write([u'[aä]', u'öption = x', '[b]', 'option = y'])
        config = self._read()
        self.assertEquals([u'aä', 'b'], config.sections())
        
        class Foo(object):
            option_c = Option(u'cä', 'option', 'value')
        
        self.assertEquals([u'aä', 'b', u'cä'], config.sections())

    def test_options(self):
        self._write(['[a]', 'option = x', '[b]', 'option = y'])
        config = self._read()
        self.assertEquals(('option', 'x'), iter(config.options('a')).next())
        self.assertEquals(('option', 'y'), iter(config.options('b')).next())
        self.assertRaises(StopIteration, iter(config.options('c')).next)
        self.assertEquals('option', iter(config['a']).next())
        self.assertEquals('option', iter(config['b']).next())
        self.assertRaises(StopIteration, iter(config['c']).next)
        
        class Foo(object):
            option_a = Option('a', 'b', 'c')
        
        self.assertEquals([('option', 'x'), ('b', 'c')],
                                list(config.options('a')))

    def test_options_unicode(self):
        self._write([u'[ä]', u'öption = x', '[b]', 'option = y'])
        config = self._read()
        self.assertEquals((u'öption', 'x'), iter(config.options(u'ä')).next())
        self.assertEquals(('option', 'y'), iter(config.options('b')).next())
        self.assertRaises(StopIteration, iter(config.options('c')).next)
        self.assertEquals(u'öption', iter(config['ä']).next())
        
        class Foo(object):
            option_a = Option(u'ä', u'öption2', 'c')
        
        self.assertEquals([(u'öption', 'x'), (u'öption2', 'c')],
                                list(config.options(u'ä')))

    def test_has_option(self):
        config = self._read()
        self.assertEquals(False, config.has_option('a', 'option'))
        self.assertEquals(False, 'option' in config['a'])
        self._write(['[a]', 'option = x'])
        config = self._read()
        self.assertEquals(True, config.has_option('a', 'option'))
        self.assertEquals(True, 'option' in config['a'])

        class Foo(object):
            option_a = Option('a', 'option2', 'x2')
        
        self.assertEquals(True, config.has_option('a', 'option2'))

    def test_has_option_unicode(self):
        config = self._read()
        self.assertEquals(False, config.has_option(u'ä', u'öption'))
        self.assertEquals(False, u'öption' in config[u'ä'])
        self._write([u'[ä]', u'öption = x'])
        config = self._read()
        self.assertEquals(True, config.has_option(u'ä', u'öption'))
        self.assertEquals(True, u'öption' in config[u'ä'])

        class Foo(object):
            option_a = Option(u'ä', u'öption2', 'x2')
        
        self.assertEquals(True, config.has_option(u'ä', u'öption2'))

    def test_reparse(self):
        self._write(['[a]', 'option = x'])
        config = self._read()
        self.assertEquals('x', config.get('a', 'option'))
        time.sleep(2) # needed because of low mtime granularity,
                      # especially on fat filesystems

        self._write(['[a]', 'option = y'])
        config.parse_if_needed()
        self.assertEquals('y', config.get('a', 'option'))

    def test_inherit_one_level(self):
        def testcb():
            config = self._read()
            self.assertEqual('x', config.get('a', 'option'))
            self.assertEqual(['a', 'inherit'], config.sections())
            config.remove('a', 'option') # Should *not* remove option in parent
            self.assertEqual('x', config.get('a', 'option'))
            self.assertEqual([('option', 'x')], list(config.options('a')))
            self.assertEqual(True, 'a' in config)
        self._test_with_inherit(testcb)


    def _test_with_inherit(self, testcb):
        sitename = os.path.join(tempfile.gettempdir(), 'trac-site.ini')
        sitefile = open(sitename, 'w')
        try:
            try:
                sitefile.write('[a]\noption = x\n')
            finally:
                sitefile.close()

            self._write(['[inherit]', 'file = trac-site.ini'])
            testcb()
        finally:
            os.remove(sitename)


def suite():
    return unittest.makeSuite(ConfigurationTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
