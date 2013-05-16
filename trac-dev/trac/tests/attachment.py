# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import unittest
import time

from trac.attachment import Attachment, AttachmentModule, \
                            LegacyAttachmentPolicy
from trac.core import Component, implements
from trac.log import logger_factory
from trac.perm import IPermissionPolicy, PermissionCache
from trac.test import EnvironmentStub, Mock
from trac.wiki.formatter import Formatter


class TicketOnlyViewsTicket(Component):
    implements(IPermissionPolicy)

    def check_permission(self, action, username, resource, perm):
        if action.startswith('TICKET_'):
            return resource.realm == 'ticket'
        else:
            return None


class AttachmentTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.env.path = os.path.join(tempfile.gettempdir(), 'trac-tempenv')
        os.mkdir(self.env.path)
        self.attachments_dir = os.path.join(self.env.path, 'attachments')
        self.env.config.set('trac', 'permission_policies',
                            'TicketOnlyViewsTicket, LegacyAttachmentPolicy')
        self.env.config.set('attachment', 'max_size', 512)

        self.perm = PermissionCache(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)
        self.env.reset_db()

    def test_get_path(self):
        attachment = Attachment(self.env, 'ticket', 42)
        attachment.filename = 'foo.txt'
        self.assertEqual(os.path.join(self.attachments_dir, 'ticket', '42',
                                      'foo.txt'),
                         attachment.path)
        attachment = Attachment(self.env, 'wiki', 'SomePage')
        attachment.filename = 'bar.jpg'
        self.assertEqual(os.path.join(self.attachments_dir, 'wiki', 'SomePage',
                                      'bar.jpg'),
                         attachment.path)

    def test_get_path_encoded(self):
        attachment = Attachment(self.env, 'ticket', 42)
        attachment.filename = 'Teh foo.txt'
        self.assertEqual(os.path.join(self.attachments_dir, 'ticket', '42',
                                      'Teh%20foo.txt'),
                         attachment.path)
        attachment = Attachment(self.env, 'wiki', u'ÜberSicht')
        attachment.filename = 'Teh bar.jpg'
        self.assertEqual(os.path.join(self.attachments_dir, 'wiki',
                                      '%C3%9CberSicht', 'Teh%20bar.jpg'),
                         attachment.path)

    def test_select_empty(self):
        self.assertRaises(StopIteration,
                          Attachment.select(self.env, 'ticket', 42).next)
        self.assertRaises(StopIteration,
                          Attachment.select(self.env, 'wiki', 'SomePage').next)

    def test_insert(self):
        attachment = Attachment(self.env, 'ticket', 42)
        attachment.insert('foo.txt', tempfile.TemporaryFile(), 0, 1)
        attachment = Attachment(self.env, 'ticket', 42)
        attachment.insert('bar.jpg', tempfile.TemporaryFile(), 0, 2)

        attachments = Attachment.select(self.env, 'ticket', 42)
        self.assertEqual('foo.txt', attachments.next().filename)
        self.assertEqual('bar.jpg', attachments.next().filename)
        self.assertRaises(StopIteration, attachments.next)

    def test_insert_unique(self):
        attachment = Attachment(self.env, 'ticket', 42)
        attachment.insert('foo.txt', tempfile.TemporaryFile(), 0)
        self.assertEqual('foo.txt', attachment.filename)
        attachment = Attachment(self.env, 'ticket', 42)
        attachment.insert('foo.txt', tempfile.TemporaryFile(), 0)
        self.assertEqual('foo.2.txt', attachment.filename)

    def test_insert_outside_attachments_dir(self):
        attachment = Attachment(self.env, '../../../../../sth/private', 42)
        self.assertRaises(AssertionError, attachment.insert, 'foo.txt',
                          tempfile.TemporaryFile(), 0)

    def test_delete(self):
        attachment1 = Attachment(self.env, 'wiki', 'SomePage')
        attachment1.insert('foo.txt', tempfile.TemporaryFile(), 0)
        attachment2 = Attachment(self.env, 'wiki', 'SomePage')
        attachment2.insert('bar.jpg', tempfile.TemporaryFile(), 0)

        attachments = Attachment.select(self.env, 'wiki', 'SomePage')
        self.assertEqual(2, len(list(attachments)))

        attachment1.delete()
        attachment2.delete()

        assert not os.path.exists(attachment1.path)
        assert not os.path.exists(attachment2.path)

        attachments = Attachment.select(self.env, 'wiki', 'SomePage')
        self.assertEqual(0, len(list(attachments)))

    def test_delete_file_gone(self):
        """
        Verify that deleting an attachment works even if the referenced file
        doesn't exist for some reason.
        """
        attachment = Attachment(self.env, 'wiki', 'SomePage')
        attachment.insert('foo.txt', tempfile.TemporaryFile(), 0)
        os.unlink(attachment.path)

        attachment.delete()

    def test_legacy_permission_on_parent(self):
        """Ensure that legacy action tests are done on parent.  As
        `ATTACHMENT_VIEW` maps to `TICKET_VIEW`, the `TICKET_VIEW` is tested
        against the ticket's resource."""
        attachment = Attachment(self.env, 'ticket', 42)
        self.assert_('ATTACHMENT_VIEW' in self.perm(attachment.resource))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AttachmentTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
