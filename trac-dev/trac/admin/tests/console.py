# -*- coding: utf-8 -*-
# 
# Copyright (C) 2004-2009 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Tim Moloney <t.moloney@verizon.net>

import ConfigParser
import difflib
import os
import re
import shlex
import sys
import time
import unittest
import traceback
from StringIO import StringIO

from trac.config import Configuration
from trac.env import Environment
from trac.admin import console
from trac.test import InMemoryDatabase
from trac.util.datefmt import get_date_format_hint

STRIP_TRAILING_SPACE = re.compile(r'( +)$', re.MULTILINE)


def load_expected_results(file, pattern):
    """Reads the file, named file, which contains test results separated by the
    regular expression pattern.

    The test results are returned as a dictionary.
    """
    expected = {}
    compiled_pattern = re.compile(pattern)
    f = open(file, 'r')
    for line in f:
        line = line.rstrip().decode('utf-8')
        match = compiled_pattern.search(line)
        if match:
            test = match.groups()[0]
            expected[test] = ''
        else:
            expected[test] += line + '\n'
    f.close()
    return expected


class InMemoryConfiguration(Configuration):
    """A subclass of Configuration that doesn't save to disk."""
    def save(self):
        pass


class InMemoryEnvironment(Environment):
    """
    A subclass of Environment that keeps its' DB in memory.
    """

    def get_db_cnx(self):
        if not hasattr(self, '_db'):
            self._db = InMemoryDatabase()
        return self._db

    def create(self, db_str=None):
        pass

    def verify(self):
        return True

    def setup_log(self):
        from trac.log import logger_factory
        self.log = logger_factory('null')

    def is_component_enabled(self, cls):
        return cls.__module__.startswith('trac.') and \
               cls.__module__.find('.tests.') == -1

    def setup_config(self, load_defaults=None):
        self.config = InMemoryConfiguration(None)


class TracadminTestCase(unittest.TestCase):
    """
    Tests the output of trac-admin and is meant to be used with
    .../trac/tests.py.
    """

    expected_results = load_expected_results(os.path.join(os.path.split(__file__)[0],
                                            'console-tests.txt'),
                                            '===== (test_[^ ]+) =====')

    def setUp(self):
        self.env = InMemoryEnvironment('', create=True)
        self.db = self.env.get_db_cnx()

        self._admin = console.TracAdmin()
        self._admin.env_set('', self.env)

        # Set test date to 11th Jan 2004
        self._test_date = '2004-01-11'

    def tearDown(self):
        self.env = None

    def _execute(self, cmd, strip_trailing_space=True, expect_exception=False):
        _err = sys.stderr
        _out = sys.stdout
        try:
            sys.stderr = sys.stdout = out = StringIO()
            setattr(out, 'encoding', 'utf-8') # fake output encoding
            retval = None
            try:
                retval = self._admin.onecmd(cmd)
            except SystemExit, e:
                pass
            sys.stderr = _err
            sys.stdout = _out
            value = out.getvalue()
            if isinstance(value, str): # reverse what print_listing did
                value = value.decode('utf-8')
            if strip_trailing_space:
                return retval, STRIP_TRAILING_SPACE.sub('', value)
            else:
                return retval, value
        except Exception, e:
            sys.stderr = _err
            sys.stdout = _out
            if expect_exception:
                tb = ''.join(traceback.format_exception(*sys.exc_info()))
                message = tb.splitlines()[-1] + '\n'
                return -1, message
            raise

    # Help test

    def test_help_ok(self):
        """
        Tests the 'help' command in trac-admin.  Since the 'help' command
        has no command arguments, it is hard to call it incorrectly.  As
        a result, there is only this one test.
        """
        from trac import __version__

        test_name = sys._getframe().f_code.co_name
        d = {'version': __version__,
             'date_format_hint': get_date_format_hint()}
        expected_results = self.expected_results[test_name] % d
        rv, output = self._execute('help')
        self.assertEqual(0, rv)
        # Create a useful delta between the output and the expected output
        output_lines = ['%s\n' % x for x in output.split('\n')]
        expected_lines = ['%s\n' % x for x in expected_results.split('\n')]
        output_diff = ''.join(list(
            difflib.unified_diff(expected_lines, output_lines)
        ))
        failure_message = "%r != %r\n" % (output, expected_results) + output_diff
        self.assertEqual(expected_results, output, failure_message)

    # Permission tests

    def test_permission_list_ok(self):
        """
        Tests the 'permission list' command in trac-admin.  Since this command
        has no command arguments, it is hard to call it incorrectly.  As
        a result, there is only this one test.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('permission list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_permission_add_one_action_ok(self):
        """
        Tests the 'permission add' command in trac-admin.  This particular
        test passes valid arguments to add one permission and checks for
        success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('permission add test_user WIKI_VIEW')
        rv, output = self._execute('permission list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_permission_add_multiple_actions_ok(self):
        """
        Tests the 'permission add' command in trac-admin.  This particular
        test passes valid arguments to add multiple permissions and checks for
        success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('permission add test_user LOG_VIEW FILE_VIEW')
        rv, output = self._execute('permission list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_permission_remove_one_action_ok(self):
        """
        Tests the 'permission remove' command in trac-admin.  This particular
        test passes valid arguments to remove one permission and checks for
        success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('permission remove anonymous TICKET_MODIFY')
        rv, output = self._execute('permission list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_permission_remove_multiple_actions_ok(self):
        """
        Tests the 'permission remove' command in trac-admin.  This particular
        test passes valid arguments to remove multiple permission and checks
        for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('permission remove anonymous WIKI_CREATE WIKI_MODIFY')
        rv, output = self._execute('permission list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    # Component tests

    def test_component_list_ok(self):
        """
        Tests the 'component list' command in trac-admin.  Since this command
        has no command arguments, it is hard to call it incorrectly.  As
        a result, there is only this one test.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('component list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_component_add_ok(self):
        """
        Tests the 'component add' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('component add new_component new_user')
        rv, output = self._execute('component list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_component_add_error_already_exists(self):
        """
        Tests the 'component add' command in trac-admin.  This particular
        test passes a component name that already exists and checks for an
        error message.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('component add component1 new_user',
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_component_rename_ok(self):
        """
        Tests the 'component rename' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('component rename component1 changed_name')
        rv, output = self._execute('component list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_component_rename_error_bad_component(self):
        """
        Tests the 'component rename' command in trac-admin.  This particular
        test tries to rename a component that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('component rename bad_component changed_name')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_component_rename_error_bad_new_name(self):
        """
        Tests the 'component rename' command in trac-admin.  This particular
        test tries to rename a component to a name that already exists.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('component rename component1 component2',
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_component_chown_ok(self):
        """
        Tests the 'component chown' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('component chown component2 changed_owner')
        rv, output = self._execute('component list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_component_chown_error_bad_component(self):
        """
        Tests the 'component chown' command in trac-admin.  This particular
        test tries to change the owner of a component that does not
        exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('component chown bad_component changed_owner')
        self.assertEqual(2, rv)
        # We currently trigger a deprecation warning with py26 so we 
        # can currrently only verify that the end of the output string is
        # correct
        self.assertEqual(output.endswith(self.expected_results[test_name]), True)

    def test_component_remove_ok(self):
        """
        Tests the 'component remove' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('component remove component1')
        rv, output = self._execute('component list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_component_remove_error_bad_component(self):
        """
        Tests the 'component remove' command in trac-admin.  This particular
        test tries to remove a component that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('component remove bad_component')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    # Ticket-type tests

    def test_ticket_type_list_ok(self):
        """
        Tests the 'ticket_type list' command in trac-admin.  Since this command
        has no command arguments, it is hard to call it incorrectly.  As
        a result, there is only this one test.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('ticket_type list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_add_ok(self):
        """
        Tests the 'ticket_type add' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('ticket_type add new_type')
        rv, output = self._execute('ticket_type list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_add_error_already_exists(self):
        """
        Tests the 'ticket_type add' command in trac-admin.  This particular
        test passes a ticket type that already exists and checks for an error
        message.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('ticket_type add defect',
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_change_ok(self):
        """
        Tests the 'ticket_type change' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('ticket_type change defect bug')
        rv, output = self._execute('ticket_type list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_change_error_bad_type(self):
        """
        Tests the 'ticket_type change' command in trac-admin.  This particular
        test tries to change a priority that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('ticket_type change bad_type changed_type')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_change_error_bad_new_name(self):
        """
        Tests the 'ticket_type change' command in trac-admin.  This particular
        test tries to change a ticket type to another type that already exists.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('ticket_type change defect task',
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_remove_ok(self):
        """
        Tests the 'ticket_type remove' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('ticket_type remove task')
        rv, output = self._execute('ticket_type list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_remove_error_bad_type(self):
        """
        Tests the 'ticket_type remove' command in trac-admin.  This particular
        test tries to remove a ticket type that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('ticket_type remove bad_type')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_order_down_ok(self):
        """
        Tests the 'ticket_type order' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('ticket_type order defect down')
        rv, output = self._execute('ticket_type list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_order_up_ok(self):
        """
        Tests the 'ticket_type order' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('ticket_type order enhancement up')
        rv, output = self._execute('ticket_type list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_ticket_type_order_error_bad_type(self):
        """
        Tests the 'priority order' command in trac-admin.  This particular
        test tries to reorder a priority that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('ticket_type order bad_type up')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    # Priority tests

    def test_priority_list_ok(self):
        """
        Tests the 'priority list' command in trac-admin.  Since this command
        has no command arguments, it is hard to call it incorrectly.  As
        a result, there is only this one test.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('priority list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_add_ok(self):
        """
        Tests the 'priority add' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('priority add new_priority')
        rv, output = self._execute('priority list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_add_many_ok(self):
        """
        Tests adding more than 10 priority values.  This makes sure that
        ordering is preserved when adding more than 10 values.
        """
        test_name = sys._getframe().f_code.co_name
        for i in xrange(11):
            self._execute('priority add p%s' % i)
        rv, output = self._execute('priority list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_add_error_already_exists(self):
        """
        Tests the 'priority add' command in trac-admin.  This particular
        test passes a priority name that already exists and checks for an
        error message.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('priority add blocker',
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_change_ok(self):
        """
        Tests the 'priority change' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('priority change major normal')
        rv, output = self._execute('priority list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_change_error_bad_priority(self):
        """
        Tests the 'priority change' command in trac-admin.  This particular
        test tries to change a priority that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('priority change bad_priority changed_name')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_change_error_bad_new_name(self):
        """
        Tests the 'priority change' command in trac-admin.  This particular
        test tries to change a priority to a name that already exists.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('priority change major minor',
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_remove_ok(self):
        """
        Tests the 'priority remove' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('priority remove major')
        rv, output = self._execute('priority list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_remove_error_bad_priority(self):
        """
        Tests the 'priority remove' command in trac-admin.  This particular
        test tries to remove a priority that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('priority remove bad_priority')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_order_down_ok(self):
        """
        Tests the 'priority order' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('priority order blocker down')
        rv, output = self._execute('priority list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_order_up_ok(self):
        """
        Tests the 'priority order' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('priority order critical up')
        rv, output = self._execute('priority list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_priority_order_error_bad_priority(self):
        """
        Tests the 'priority order' command in trac-admin.  This particular
        test tries to reorder a priority that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('priority remove bad_priority')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    # Severity tests

    def test_severity_list_ok(self):
        """
        Tests the 'severity list' command in trac-admin.  Since this command
        has no command arguments, it is hard to call it incorrectly.  As
        a result, there is only this one test.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('severity list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_add_ok(self):
        """
        Tests the 'severity add' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('severity add new_severity')
        rv, output = self._execute('severity list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_add_error_already_exists(self):
        """
        Tests the 'severity add' command in trac-admin.  This particular
        test passes a severity name that already exists and checks for an
        error message.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('severity add blocker')
        rv, output = self._execute('severity add blocker',
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_change_ok(self):
        """
        Tests the 'severity add' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('severity add critical')
        self._execute('severity change critical "end-of-the-world"')
        rv, output = self._execute('severity list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_change_error_bad_severity(self):
        """
        Tests the 'severity change' command in trac-admin.  This particular
        test tries to change a severity that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('severity change bad_severity changed_name')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_change_error_bad_new_name(self):
        """
        Tests the 'severity change' command in trac-admin.  This particular
        test tries to change a severity to a name that already exists.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('severity add major')
        self._execute('severity add critical')
        rv, output = self._execute('severity change critical major',
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_remove_ok(self):
        """
        Tests the 'severity add' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('severity remove trivial')
        rv, output = self._execute('severity list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_remove_error_bad_severity(self):
        """
        Tests the 'severity remove' command in trac-admin.  This particular
        test tries to remove a severity that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('severity remove bad_severity')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_order_down_ok(self):
        """
        Tests the 'severity order' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('severity add foo')
        self._execute('severity add bar')
        self._execute('severity order foo down')
        rv, output = self._execute('severity list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_order_up_ok(self):
        """
        Tests the 'severity order' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('severity add foo')
        self._execute('severity add bar')
        self._execute('severity order bar up')
        rv, output = self._execute('severity list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_severity_order_error_bad_severity(self):
        """
        Tests the 'severity order' command in trac-admin.  This particular
        test tries to reorder a priority that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('severity remove bad_severity')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    # Version tests

    def test_version_list_ok(self):
        """
        Tests the 'version list' command in trac-admin.  Since this command
        has no command arguments, it is hard to call it incorrectly.  As
        a result, there is only this one test.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('version list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_add_ok(self):
        """
        Tests the 'version add' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('version add 9.9 "%s"' % self._test_date)
        rv, output = self._execute('version list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_add_error_already_exists(self):
        """
        Tests the 'version add' command in trac-admin.  This particular
        test passes a version name that already exists and checks for an
        error message.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('version add 1.0 "%s"' % self._test_date,
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_rename_ok(self):
        """
        Tests the 'version rename' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('version rename 1.0 9.9')
        rv, output = self._execute('version list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_rename_error_bad_version(self):
        """
        Tests the 'version rename' command in trac-admin.  This particular
        test tries to rename a version that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('version rename bad_version changed_name')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_time_ok(self):
        """
        Tests the 'version time' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('version time 2.0 "%s"' % self._test_date)
        rv, output = self._execute('version list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_time_unset_ok(self):
        """
        Tests the 'version time' command in trac-admin.  This particular
        test passes valid arguments for unsetting the date.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('version time 2.0 "%s"' % self._test_date)
        self._execute('version time 2.0 ""')
        rv, output = self._execute('version list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_time_error_bad_version(self):
        """
        Tests the 'version time' command in trac-admin.  This particular
        test tries to change the time on a version that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('version time bad_version "%s"'
                                   % self._test_date)
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_remove_ok(self):
        """
        Tests the 'version remove' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('version remove 1.0')
        rv, output = self._execute('version list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_version_remove_error_bad_version(self):
        """
        Tests the 'version remove' command in trac-admin.  This particular
        test tries to remove a version that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('version remove bad_version')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    # Milestone tests

    def test_milestone_list_ok(self):
        """
        Tests the 'milestone list' command in trac-admin.  Since this command
        has no command arguments, it is hard to call it incorrectly.  As
        a result, there is only this one test.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('milestone list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_add_ok(self):
        """
        Tests the 'milestone add' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('milestone add new_milestone "%s"' % self._test_date)
        rv, output = self._execute('milestone list')
        #self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_add_utf8_ok(self):
        """
        Tests the 'milestone add' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute(u'milestone add \xe9tat_final "%s"'  #\xc3\xa9
                              % self._test_date)
        rv, output = self._execute('milestone list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_add_error_already_exists(self):
        """
        Tests the 'milestone add' command in trac-admin.  This particular
        test passes a milestone name that already exists and checks for an
        error message.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('milestone add milestone1 "%s"'
                                   % self._test_date,
                                   expect_exception=True)
        self.assertEqual(-1, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_rename_ok(self):
        """
        Tests the 'milestone rename' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('milestone rename milestone1 changed_milestone')
        rv, output = self._execute('milestone list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_rename_error_bad_milestone(self):
        """
        Tests the 'milestone rename' command in trac-admin.  This particular
        test tries to rename a milestone that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('milestone rename bad_milestone changed_name')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_due_ok(self):
        """
        Tests the 'milestone due' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('milestone due milestone2 "%s"' % self._test_date)
        rv, output = self._execute('milestone list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_due_unset_ok(self):
        """
        Tests the 'milestone due' command in trac-admin.  This particular
        test passes valid arguments for unsetting the due date.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('milestone due milestone2 "%s"' % self._test_date)
        self._execute('milestone due milestone2 ""')
        rv, output = self._execute('milestone list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_due_error_bad_milestone(self):
        """
        Tests the 'milestone due' command in trac-admin.  This particular
        test tries to change the due date on a milestone that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('milestone due bad_milestone "%s"'
                                   % self._test_date)
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_completed_ok(self):
        """
        Tests the 'milestone completed' command in trac-admin.  This particular
        test passes valid arguments and checks for success.
        """
        test_name = sys._getframe().f_code.co_name

        self._execute('milestone completed milestone2 "%s"' % self._test_date)
        rv, output = self._execute('milestone list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_completed_error_bad_milestone(self):
        """
        Tests the 'milestone completed' command in trac-admin.  This particular
        test tries to change the completed date on a milestone that does not
        exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('milestone completed bad_milestone "%s"'
                                   % self._test_date)
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_remove_ok(self):
        """
        Tests the 'milestone remove' command in trac-admin.  This particular
        test passes a valid argument and checks for success.
        """
        test_name = sys._getframe().f_code.co_name
        self._execute('milestone remove milestone3')
        rv, output = self._execute('milestone list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_milestone_remove_error_bad_milestone(self):
        """
        Tests the 'milestone remove' command in trac-admin.  This particular
        test tries to remove a milestone that does not exist.
        """
        test_name = sys._getframe().f_code.co_name
        rv, output = self._execute('milestone remove bad_milestone')
        self.assertEqual(2, rv)
        self.assertEqual(self.expected_results[test_name], output)

    def test_backslash_use_ok(self):
        test_name = sys._getframe().f_code.co_name
        if self._admin.interactive:
            self._execute('version add \\')
        else:
            self._execute(r"version add '\'")
        rv, output = self._execute('version list')
        self.assertEqual(0, rv)
        self.assertEqual(self.expected_results[test_name], output)


def suite():
    return unittest.makeSuite(TracadminTestCase, 'test')

if __name__ == '__main__':
    unittest.main()
