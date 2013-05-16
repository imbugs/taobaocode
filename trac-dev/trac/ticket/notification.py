# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2009 Edgewall Software
# Copyright (C) 2003-2005 Daniel Lundin <daniel@edgewall.com>
# Copyright (C) 2005-2006 Emmanuel Blot <emmanuel.blot@free.fr>
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
# Author: Daniel Lundin <daniel@edgewall.com>
#

from trac import __version__
from trac.core import *
from trac.config import *
from trac.notification import NotifyEmail
from trac.util import md5
from trac.util.datefmt import to_timestamp
from trac.util.text import CRLF, wrap, to_unicode, obfuscate_email_address

from genshi.template.text import TextTemplate

class TicketNotificationSystem(Component):

    always_notify_owner = BoolOption('notification', 'always_notify_owner',
                                     'false',
        """Always send notifications to the ticket owner (''since 0.9'').""")

    always_notify_reporter = BoolOption('notification', 'always_notify_reporter',
                                        'false',
        """Always send notifications to any address in the ''reporter''
        field.""")

    always_notify_updater = BoolOption('notification', 'always_notify_updater',
                                       'true',
        """Always send notifications to the person who causes the ticket 
        property change and to any previous updater of that ticket.""")
        
    ticket_subject_template = Option('notification', 'ticket_subject_template', 
                                     '$prefix #$ticket.id: $summary',
        """A Genshi text template snippet used to get the notification subject.

        By default, the subject template is `$prefix #$ticket.id: $summary`.
        `$prefix` being the value of the `smtp_subject_prefix` option.
        ''(since 0.11)''""")


class TicketNotifyEmail(NotifyEmail):
    """Notification of ticket changes."""

    template_name = "ticket_notify_email.txt"
    ticket = None
    newticket = None
    modtime = 0
    from_email = 'trac+ticket@localhost'
    COLS = 75

    def __init__(self, env):
        NotifyEmail.__init__(self, env)
        self.prev_cc = []

    def notify(self, ticket, newticket=True, modtime=None):
        self.ticket = ticket
        self.modtime = modtime
        self.newticket = newticket

        changes_body = ''
        self.reporter = ''
        self.owner = ''
        changes_descr = ''
        change_data = {}
        link = self.env.abs_href.ticket(ticket.id)
        summary = self.ticket['summary']
        
        if not self.newticket and modtime:  # Ticket change
            from trac.ticket.web_ui import TicketModule
            for change in TicketModule(self.env).grouped_changelog_entries(
                ticket, self.db, when=modtime):
                if not change['permanent']: # attachment with same time...
                    continue
                change_data.update({
                    'author': obfuscate_email_address(change['author']),
                    'comment': wrap(change['comment'], self.COLS, ' ', ' ',
                                    CRLF)
                    })
                link += '#comment:%s' % str(change.get('cnum', ''))
                for field, values in change['fields'].iteritems():
                    old = values['old']
                    new = values['new']
                    newv = ''
                    if field == 'description':
                        new_descr = wrap(new, self.COLS, ' ', ' ', CRLF)
                        old_descr = wrap(old, self.COLS, '> ', '> ', CRLF)
                        old_descr = old_descr.replace(2*CRLF, CRLF + '>' + \
                                                      CRLF)
                        cdescr = CRLF
                        cdescr += 'Old description:' + 2*CRLF + old_descr + \
                                  2*CRLF
                        cdescr += 'New description:' + 2*CRLF + new_descr + \
                                  CRLF
                        changes_descr = cdescr
                    elif field == 'summary':
                        summary = "%s (was: %s)" % (new, old)
                    elif field == 'cc':
                        (addcc, delcc) = self.diff_cc(old, new)
                        chgcc = ''
                        if delcc:
                            chgcc += wrap(" * cc: %s (removed)" %
                                          ', '.join(delcc), 
                                          self.COLS, ' ', ' ', CRLF) + CRLF
                        if addcc:
                            chgcc += wrap(" * cc: %s (added)" %
                                          ', '.join(addcc), 
                                          self.COLS, ' ', ' ', CRLF) + CRLF
                        if chgcc:
                            changes_body += chgcc
                        self.prev_cc += old and self.parse_cc(old) or []
                    else:
                        if field in ['owner', 'reporter']:
                            old = obfuscate_email_address(old)
                            new = obfuscate_email_address(new)
                        newv = new
                        l = 7 + len(field)
                        chg = wrap('%s => %s' % (old, new), self.COLS - l, '',
                                   l * ' ', CRLF)
                        changes_body += '  * %s:  %s%s' % (field, chg, CRLF)
                    if newv:
                        change_data[field] = {'oldvalue': old, 'newvalue': new}
            
        self.ticket['description'] = wrap(
            self.ticket.values.get('description', ''), self.COLS,
            initial_indent=' ', subsequent_indent=' ', linesep=CRLF)
        self.ticket['new'] = self.newticket
        self.ticket['link'] = link
        
        subject = self.format_subj(summary)
        if not self.newticket:
            subject = 'Re: ' + subject
        self.data.update({
            'ticket_props': self.format_props(),
            'ticket_body_hdr': self.format_hdr(),
            'subject': subject,
            'ticket': ticket.values,
            'changes_body': changes_body,
            'changes_descr': changes_descr,
            'change': change_data
            })
        NotifyEmail.notify(self, ticket.id, subject)

    def format_props(self):
        tkt = self.ticket
        fields = [f for f in tkt.fields if f['name'] not in ('summary', 'cc')]
        width = [0, 0, 0, 0]
        i = 0
        for f in [f['name'] for f in fields if f['type'] != 'textarea']:
            if not tkt.values.has_key(f):
                continue
            fval = tkt[f] or ''
            if fval.find('\n') != -1:
                continue
            idx = 2 * (i % 2)
            if len(f) > width[idx]:
                width[idx] = len(f)
            if len(fval) > width[idx + 1]:
                width[idx + 1] = len(fval)
            i += 1
        format = ('%%%is:  %%-%is  |  ' % (width[0], width[1]),
                  ' %%%is:  %%-%is%s' % (width[2], width[3], CRLF))
        l = (width[0] + width[1] + 5)
        sep = l * '-' + '+' + (self.COLS - l) * '-'
        txt = sep + CRLF
        big = []
        i = 0
        for f in [f for f in fields if f['name'] != 'description']:
            fname = f['name']
            if not tkt.values.has_key(fname):
                continue
            fval = tkt[fname] or ''
            if fname in ['owner', 'reporter']:
                fval = obfuscate_email_address(fval)
            if f['type'] == 'textarea' or '\n' in unicode(fval):
                big.append((fname.capitalize(), CRLF.join(fval.splitlines())))
            else:
                txt += format[i % 2] % (fname.capitalize(), fval)
                i += 1
        if i % 2:
            txt += CRLF
        if big:
            txt += sep
            for name, value in big:
                txt += CRLF.join(['', name + ':', value, '', ''])
        txt += sep
        return txt

    def parse_cc(self, txt):
        return filter(lambda x: '@' in x, txt.replace(',', ' ').split())

    def diff_cc(self, old, new):
        oldcc = NotifyEmail.addrsep_re.split(old)
        newcc = NotifyEmail.addrsep_re.split(new)
        added = [obfuscate_email_address(x) \
                                for x in newcc if x and x not in oldcc]
        removed = [obfuscate_email_address(x) \
                                for x in oldcc if x and x not in newcc]
        return (added, removed)

    def format_hdr(self):
        return '#%s: %s' % (self.ticket.id, wrap(self.ticket['summary'],
                                                 self.COLS, linesep=CRLF))

    def format_subj(self, summary):
        template = self.config.get('notification','ticket_subject_template')
        template = TextTemplate(template.encode('utf8'))
                                                
        prefix = self.config.get('notification', 'smtp_subject_prefix')
        if prefix == '__default__': 
            prefix = '[%s]' % self.config.get('project', 'name')
        
        data = {
            'prefix': prefix,
            'summary': summary,
            'ticket': self.ticket,
            'env': self.env,
        }
        
        return template.generate(**data).render('text', encoding=None).strip()

    def get_recipients(self, tktid):
        notify_reporter = self.config.getbool('notification',
                                              'always_notify_reporter')
        notify_owner = self.config.getbool('notification',
                                           'always_notify_owner')
        notify_updater = self.config.getbool('notification', 
                                             'always_notify_updater')

        ccrecipients = self.prev_cc
        torecipients = []
        cursor = self.db.cursor()
        
        # Harvest email addresses from the cc, reporter, and owner fields
        cursor.execute("SELECT cc,reporter,owner FROM ticket WHERE id=%s",
                       (tktid,))
        row = cursor.fetchone()
        if row:
            ccrecipients += row[0] and row[0].replace(',', ' ').split() or []
            self.reporter = row[1]
            self.owner = row[2]
            if notify_reporter:
                torecipients.append(row[1])
            if notify_owner:
                torecipients.append(row[2])

        # Harvest email addresses from the author field of ticket_change(s)
        if notify_updater:
            cursor.execute("SELECT DISTINCT author,ticket FROM ticket_change "
                           "WHERE ticket=%s", (tktid,))
            for author,ticket in cursor:
                torecipients.append(author)

        # Suppress the updater from the recipients
        updater = None
        cursor.execute("SELECT author FROM ticket_change WHERE ticket=%s "
                       "ORDER BY time DESC LIMIT 1", (tktid,))
        for updater, in cursor:
            break
        else:
            cursor.execute("SELECT reporter FROM ticket WHERE id=%s",
                           (tktid,))
            for updater, in cursor:
                break

        if not notify_updater:
            filter_out = True
            if notify_reporter and (updater == self.reporter):
                filter_out = False
            if notify_owner and (updater == self.owner):
                filter_out = False
            if filter_out:
                torecipients = [r for r in torecipients if r and r != updater]
        elif updater:
            torecipients.append(updater)

        return (torecipients, ccrecipients)

    def get_message_id(self, rcpt, modtime=None):
        """Generate a predictable, but sufficiently unique message ID."""
        s = '%s.%08d.%d.%s' % (self.config.get('project', 'url'),
                               int(self.ticket.id), to_timestamp(modtime),
                               rcpt.encode('ascii', 'ignore'))
        dig = md5(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        msgid = '<%03d.%s@%s>' % (len(s), dig, host)
        return msgid

    def send(self, torcpts, ccrcpts):
        dest = self.reporter or 'anonymous'
        hdrs = {}
        hdrs['Message-ID'] = self.get_message_id(dest, self.modtime)
        hdrs['X-Trac-Ticket-ID'] = str(self.ticket.id)
        hdrs['X-Trac-Ticket-URL'] = self.ticket['link']
        if not self.newticket:
            msgid = self.get_message_id(dest)
            hdrs['In-Reply-To'] = msgid
            hdrs['References'] = msgid
        NotifyEmail.send(self, torcpts, ccrcpts, hdrs)

