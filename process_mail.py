#!/usr/bin/env python
import sys
sys.path.append("/home/seb/Code/")
import os; os.environ["DJANGO_SETTINGS_MODULE"] = "mailtrail.settings"
from django.core.management import setup_environ
import settings
setup_environ(settings)

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename="/tmp/mailtrail.log",
                    filemode="w")

import email
from email.utils import parseaddr

from mail.models import Organisation
from mail.models import CustomUser
from mail.models import Mail

# Postfix error codes:
EX_NOINPUT = 66 # Cannot open input
EX_NOUSER = 67 # Addressee unknown
EX_SOFTWARE = 70 # Internal software error


def get_charset(message, default="ascii"):
    """Get the message charset"""
    if message.get_content_charset():
        return message.get_content_charset()
    if message.get_charset():
        return message.get_charset()
    return default

def make_response_from_file(fp):
    parsed_email = email.message_from_file(fp)
    logging.debug("Received email\n--------\n%s--------\n"\
                  % parsed_email.as_string())
    try:
        return make_response_from_email(parsed_email)
    except (KeyError, AttributeError):
        logging.error("Couldn't handle\n--------\n%s--------\n"\
                      % parsed_email.as_string())
        return EX_SOFTWARE
        
def make_response_from_email(parsed_email):
    name, mto = parseaddr(parsed_email['to'])
    proxy_email_id = mto[:mto.find("@")]
    proxy_email_id = proxy_email_id.replace(settings.MAIL_PREFIX, "")
    message_id = parsed_email['message-id']\
                 .replace("<", "")\
                 .replace(">", "")
    logging.debug("Looking for proxy_email of %s" % proxy_email_id)
    try:
        user = CustomUser.objects.get(proxy_email_id=proxy_email_id)
        in_reply_to = None

        # http://www.jwz.org/doc/threading.html
        references = parsed_email.get('references','').split(" ")
        in_reply_to_id = parsed_email.get('in-reply-to','')
        if in_reply_to_id:
            references.append(in_reply_to_id)
        tmp = []
        for ref in references:
            tmp.append(ref.replace("<", "").replace(">", ""))
        references = tmp
        logging.debug("Possible references in thread: %s"\
                      % ", ".join(ref))
        in_reply_to = None
        for ref in references:
            try:
                in_reply_to = Mail.objects.get(
                    message_id=ref)
            except Mail.DoesNotExist:
                continue
        # XXX in here, we should do some heuristics to thread on
        # Subject in the case where in_reply_to wasn't found
        # - strip Re:, RE:, RE[5]:, "Re: Re" etc first
        if in_reply_to:
            name, mfrom = parseaddr(parsed_email['from'])
            mfrom, created = CustomUser.objects.get_or_create(email=mfrom)
            if created:
                if not in_reply_to.mto.organisation:
                    name = mfrom.email[mfrom.email.find('@')+1:]
                    in_reply_to.mto.organisation = \
                               Organisation.objects.create(name=name)
                    in_reply_to.mto.save()
                mfrom.organisation = in_reply_to.mto.organisation
                mfrom.save()
            mto = user
            counter = 1
            for part in parsed_email.walk():
                if part.get_content_maintype() == "multipart":
                    continue # it's just a container
                filename = part.get_filename()
                counter += 1
                # XXX the following needs to change to save all parts
                # of a message
                # for unicoding stuff, see
                # http://ginstrom.com/scribbles/2007/11/19/parsing-multilingual-email-with-python/ 
                if part.get_content_type() == "text/plain":
                    charset = get_charset(part, get_charset(parsed_email))
                    message = unicode(part.get_payload(decode=True),
                                      charset,
                                      "replace")
                    break
                else:
                    message = "unknown"
            newmsg = Mail.objects.create(subject=parsed_email['subject'],
                                         mfrom=mfrom,
                                         mto=mto,
                                         message=message,
                                         in_reply_to=in_reply_to,
                                         message_id=message_id)
            return newmsg
        else:
            logging.warn("Couldn't find thread for %s" % message_id)
            return EX_SOFTWARE 

    except CustomUser.DoesNotExist:
        logging.warn("Couldn't find addressee %s" % message_id)
        return EX_NOUSER 

if __name__ == "__main__":
    parsed_email = make_response_from_file(sys.stdin)
    if isinstance(parsed_email, Mail):
        sys.exit(0)
    else:
        sys.exit(parsed_email)
