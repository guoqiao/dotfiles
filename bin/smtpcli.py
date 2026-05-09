#!/usr/bin/env python3
"""
Send Email via SMTP from CLI with Python.

Goal:
- Load credentials from config file for security.
- Send text/html email
- Support cc, bcc, reply-to
- Read email body from file
- Send attachments
- Send all files in a directory as attachments

Author: guoqiao <guoqiao@gmail.com>
"""
import os
import json
import logging
import smtplib
from io import open
from os import environ as env
from os import getenv

import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

# file name without ext
APP_NAME = os.path.basename(__file__).split('.')[0]
log = logging.getLogger(APP_NAME)

# search for first existing config
CONFIG_PATHS = [
    '~/.{}.json'.format(APP_NAME),
    '~/.config/{}.json'.format(APP_NAME),
    '/etc/{}.json'.format(APP_NAME),
]

# example config file:
"""
"default": {
    "username": "FOO@bar.com",
    "password": "password",
    "host": "smtp.gmail.com",
    "port": 25,
    "mode": "Plain"
},
"gmail": {
    "username": "FOO@gmail.com",
    "password": "qwerty",
    "host": "smtp.gmail.com",
    "port": 465,
    "mode": "SSL"
},
"outlook": {
    "username": "NAME@outlook.com",
    "password": "123456",
    "host": "smtp-mail.outlook.com",
    "port": 587,
    "mode": "STARTTLS"
}
"""

SMTP_MODE_PLAIN = 'Plain'
SMTP_MODE_STARTTLS = 'STARTTLS'
SMTP_MODE_SSL = 'SSL'

SMTP_MODE_CHOICES = (
    SMTP_MODE_PLAIN,
    SMTP_MODE_STARTTLS,
    SMTP_MODE_SSL,
)


def get_list(value, sep=','):
    """Get a list from value"""
    if not value:
        return []
    if isinstance(value, str):  # single or comma separated
        return value.strip().strip(sep).split(sep)
    return value


def read_path(path):
    """
    Read file content at path if possible.
    """
    if path and len(path.splitlines()) == 1:
        path = os.path.expandvars(os.path.expanduser(path))
        if os.path.isfile(path):
            return open(path, mode='rt').read()
    return ''


class Config(object):

    def __init__(self):
        self.data = self.load()
        log.debug('config data: %s', self.data)

    def load(self):
        for path in CONFIG_PATHS:
            path = os.path.expandvars(os.path.expanduser(path))
            if os.path.isfile(path):
                with open(path, mode='rt') as conf_file:
                    log.debug('loading config from %s', path)
                    return json.load(conf_file)
        log.error('no config file found')
        return {}

    def get_account(self, name='default'):
        account_config = self.data.get(name, {})
        log.debug('using account %s: %s', name, account_config)
        return account_config


def get_smtp_client(account, debuglevel=False):
    """
    Get SMTP connection.

    account example:

        {
            "username": "FOO@bar.com",
            "password": "password",
            "host": "smtp.gmail.com",
            "port": 25,
            "mode": "Plain"
        }

    common mode and port:
    Plain: 25
    TLS: 465
    StartTLS: 587
    """
    host = account['host']
    port = account['port']
    mode = account['mode']

    if mode == SMTP_MODE_PLAIN:
        client = smtplib.SMTP(host, port)
    elif mode == SMTP_MODE_STARTTLS:
        client = smtplib.SMTP(host, port)
        client.starttls()
    else:
        client = smtplib.SMTP_SSL(host, port)

    client.login(account['username'], account['password'])
    client.set_debuglevel(debuglevel)
    return client


def build_mime_msg(path, filename=''):
    """Build MIME Message from path"""

    # set filename with /path/to/file:filename
    if ':' in path:
        path, filename = path.rsplit(':', 1)

    if not os.path.isfile(path):
        log.warn('skip invalid attachment: %s', path)
        return None

    ctype, encoding = mimetypes.guess_type(path)
    if ctype is None or encoding is not None:
        # No guess could be made, or the file is encoded (compressed), so
        # use a generic bag-of-bits type.
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    log.debug('attachment ctype: %s', ctype)
    if maintype == 'text':
        with open(path, 'rt') as fp:
            msg = MIMEText(fp.read(), _subtype=subtype, _charset='utf-8')
    elif maintype == 'image':
        with open(path, 'rb') as fp:
            msg = MIMEImage(fp.read(), _subtype=subtype)
    elif maintype == 'audio':
        with open(path, 'rb') as fp:
            msg = MIMEAudio(fp.read(), _subtype=subtype)
    else:
        msg = MIMEBase(maintype, subtype)
        with open(path, 'rb') as fp:
            msg.set_payload(fp.read())
        encoders.encode_base64(msg)  # Encode the payload using Base64
    # Set the filename parameter
    filename = filename or os.path.basename(path)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    return msg


def build_mail_msg(
        from_=None, to=None, cc=None, bcc=None, reply_to=None,
        subject=None, extra_headers=None,
        text=None, html=None, attachments=None):

    headers = {
        'From': from_,
        'To': to,
        'Cc': cc,
        'Bcc': bcc,
        'Reply-To': reply_to,
        'Subject': subject,
    }

    if extra_headers:
        headers.update(extra_headers)

    if not any([text, html, attachments]):
        # no content, send a text to help test
        text = 'this is a test mail'

    # if text is a path, then read file context as text
    content = read_path(text)
    if content:
        log.debug('read text content from %s: \n\n%s\n\n', text, content)
        text = content

    content = read_path(html)
    if content:
        log.debug('read html content from %s: \n\n%s\n\n', html, content)
        html = content

    root = MIMEMultipart('alternative')

    for name, value in headers.items():
        if value:
            if isinstance(value, (list, tuple)):
                value = ','.join(value)
            root[name] = str(value)
            log.debug('add header %s: %s', name, value)

    if text:
        root.attach(MIMEText(text, _subtype='plain', _charset='utf-8'))
    if html:
        root.attach(MIMEText(html, _subtype='html', _charset='utf-8'))

    files = set([])
    for path in attachments or []:
        path = os.path.expandvars(os.path.expanduser(path))
        if os.path.isfile(path):
            files.add(path)
        elif os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    files.add(os.path.join(dirpath, filename))

    n = 1
    for path in files:  # limit files
        msg = build_mime_msg(path)
        if msg:
            log.info('Attachment %02d: %s', n, path)
            root.attach(msg)
            n += 1
            if n >= 20:
                log.warning('too many files, only 20 attached')
                break

    return root.as_string()


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Send Mail via SMTP from CLI')
    email_options = parser.add_argument_group('Email Options')

    email_options.add_argument(
        '-a', '--account', default='default',
        help='account name defined in config file to load credentials from')

    email_options.add_argument(
        '--from', dest='from_', metavar='EMAIL_FROM', default='',
        help=('From email address only for display in message, leave it blank to use account username'))

    email_options.add_argument(
        '--to', metavar='EMAIL_TO', default=[], action='append',
        help='To email address, can be repeated, leave it blank to use from address')

    email_options.add_argument(
        '--cc', metavar='EMAIL_CC', default=[], action='append',
        help='CC email address, can be repeated')

    email_options.add_argument(
        '--bcc', metavar='EMAIL_BCC', default=[], action='append',
        help='BCC email address, can be repeated')

    email_options.add_argument(
        '--reply-to', metavar='EMAIL_REPLY_TO', dest='reply_to', default='',
        help='Reply-To email address')

    email_options.add_argument(
        '-s', '--subject', metavar='EMAIL_SUBJECT',
        default='test mail from %s' % APP_NAME,
        help='email subject')

    email_options.add_argument(
        '--text', metavar='EMAIL_TEXT',
        help='email content text version, could be a file path to read from')

    email_options.add_argument(
        '--html', metavar='EMAIL_HTML',
        help='email content html version')

    email_options.add_argument(
        '-A', '--attachment', metavar='ATTACHMENT',
        action='append', default=[], dest='attachments',
        help='attachment path, can be repeated, can be file or dir')

    log_options = parser.add_mutually_exclusive_group(required=False)
    log_options.add_argument(
        '-v', '--verbose', action='store_true',
        help='Print debug logs')
    log_options.add_argument(
        '-q', '--quiet', action='store_true',
        help='Only print error logs')

    return parser.parse_args()


def main():
    args = parse_args()
    log.debug(args)

    level = (args.verbose and logging.DEBUG or
             args.quiet and logging.ERROR or
             logging.INFO)
    logging.basicConfig(level=level)

    account = Config().get_account(args.account)
    from_ = args.from_ or account['username']  # fall back to username
    to = args.to or [from_]  # fall back to from addr

    message = build_mail_msg(
        from_=from_, to=to, cc=args.cc, reply_to=args.reply_to,
        subject=args.subject,
        text=args.text, html=args.html,
        attachments=args.attachments)

    log.debug('sendmail begin\n')
    debug = args.verbose and not args.attachments
    with get_smtp_client(account, debuglevel=debug) as client:
        recipients = to + args.cc + args.bcc
        client.sendmail(from_, recipients, message)
    log.debug('sendmail end\n')


if __name__ == '__main__':
    main()
