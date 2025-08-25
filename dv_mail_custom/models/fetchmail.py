# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
import imaplib
import logging
import poplib
import socket

from imaplib import IMAP4, IMAP4_SSL
from poplib import POP3, POP3_SSL
from socket import gaierror, timeout
from ssl import SSLError

from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60

# Workaround for Python 2.7.8 bug https://bugs.python.org/issue23906
# poplib._MAXLINE = 65536

# # Add timeout to IMAP connections
# # HACK https://bugs.python.org/issue38615
# # TODO: clean in Python 3.9
# IMAP4._create_socket = lambda self, timeout=MAIL_TIMEOUT: socket.create_connection((self.host or None, self.port), timeout)


# def make_wrap_property(name):
#     return property(
#         lambda self: getattr(self.__obj__, name),
#         lambda self, value: setattr(self.__obj__, name, value),
#     )


# class IMAP4Connection:
#     """Wrapper around IMAP4 and IMAP4_SSL"""
#     def __init__(self, server, port, is_ssl):
#         self.__obj__ = IMAP4_SSL(server, port) if is_ssl else IMAP4(server, port)

# class POP3Connection:
#     """Wrapper around POP3 and POP3_SSL"""
#     def __init__(self, server, port, is_ssl, timeout=MAIL_TIMEOUT):
#         self.__obj__ = POP3_SSL(server, port, timeout=timeout) if is_ssl else POP3(server, port, timeout=timeout)


class FetchmailServer(models.Model):
    #_name = 'fetchmail.server'
    _inherit = 'fetchmail.server'

    def fetch_mail(self):
        _logger.info("FETCH MAIL")
        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.server_type, server.name)
            additionnal_context['default_fetchmail_server_id'] = server.id
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            result = None
            connection_type = server._get_connection_type()
            if connection_type == 'imap':
                try:
                    imap_server = server.connect()
                    _logger.info("IMP_SERVER: %d", imap_server)
                    imap_server.select()
                    result, data = imap_server.search(None, '(UNSEEN)')
                    _logger.info("RESULT Y DATA: %d; %d", result, data)
                    for num in data[0].split():
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        _logger.info("RESULTADO: %d", result)
                        imap_server.store(num, '-FLAGS', '\\Seen')
                        try:
                            _logger.info("CREANDO MENSAGE")
                            res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, data[0][1], save_original=server.original, strip_attachments=(not server.attach))
                        except Exception:
                            _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                            failed += 1
                        imap_server.store(num, '+FLAGS', '\\Seen')
                        self._cr.commit()
                        count += 1
                    _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if imap_server:
                        try:
                            imap_server.close()
                            imap_server.logout()
                        except OSError:
                            _logger.warning('Failed to properly finish imap connection: %s.', server.name, exc_info=True)
            elif connection_type == 'pop':
                try:
                    while True:
                        failed_in_loop = 0
                        num = 0
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            res_id = None
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach))
                                pop_server.dele(num)
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                                failed += 1
                                failed_in_loop += 1
                            self.env.cr.commit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num, server.server_type, server.name, (num - failed_in_loop), failed_in_loop)
                        # Stop if (1) no more message left or (2) all messages have failed
                        if num_messages < MAX_POP_MESSAGES or failed_in_loop == num:
                            break
                        pop_server.quit()
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        try:
                            pop_server.quit()
                        except OSError:
                            _logger.warning('Failed to properly finish pop connection: %s.', server.name, exc_info=True)
            server.write({'date': fields.Datetime.now()})
        if result:
            return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Mensaje',
                            'message': result + ", " + str(imap_server),
                            'sticky': False,
                        },
                    }
        else:
            return True
    
    # def connect(self, allow_archived=False):
    #     """
    #     :param bool allow_archived: by default (False), an exception is raised when calling this method on an
    #        archived record. It can be set to True for testing so that the exception is no longer raised.
    #     """
    #     self.ensure_one()
    #     if not allow_archived and not self.active:
    #         raise UserError(_('The server "%s" cannot be used because it is archived.', self.display_name))
    #     connection_type = self._get_connection_type()
    #     if connection_type == 'imap':
    #         connection = IMAP4Connection(self.server, int(self.port), self.is_ssl)
    #         self._imap_login(connection)
    #     elif connection_type == 'pop':
    #         connection = POP3Connection(self.server, int(self.port), self.is_ssl)
    #         #TODO: use this to remove only unread messages
    #         #connection.user("recent:"+server.user)
    #         connection.user(self.user)
    #         connection.pass_(self.password)
    #     print("CONEXIONNN: ", connection)
    #     return connection

    # def _imap_login(self, connection):
    #     """Authenticate the IMAP connection.

    #     If the mail server is Gmail, we use the OAuth2 authentication protocol.
    #     """
    #     self.ensure_one()
    #     print("OOOOOO---- ", self.server_type)
    #     if self.server_type == 'gmail':
    #         print("AAAAAAAAA")
    #         auth_string = self._generate_oauth2_string(self.user, self.google_gmail_refresh_token)
    #         con = connection.authenticate('XOAUTH2', lambda x: auth_string)
    #         connection.select('INBOX')
    #         print(con)
    #     else:
    #         super(FetchmailServer, self)._imap_login(connection)

    # def _get_connection_type(self):
    #     """Return which connection must be used for this mail server (IMAP or POP).
    #     The Gmail mail server used an IMAP connection.
    #     """
    #     self.ensure_one()
    #     return 'imap' if self.server_type == 'gmail' else super()._get_connection_type()
