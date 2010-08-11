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

from django.db.models import Q
import email
from email.utils import parseaddr

from mail.models import Organisation
from mail.models import CustomUser
from mail.models import Mail
from utils import send_mail
from utils import strip_re

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
    logging.debug("Received email\n--------\n%s\n--------"\
                  % parsed_email.as_string())
    try:
        return make_response_from_email(parsed_email)
    except (KeyError, AttributeError):
        logging.error("Couldn't handle\n--------\n%s\n--------"\
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
        to_user = CustomUser.objects.get(
            proxy_email_id=proxy_email_id)
        in_reply_to = None
        # http://www.jwz.org/doc/threading.html
        references = parsed_email.get('references','')
        references = references and references.split(" ") or []
        in_reply_to_id = parsed_email.get('in-reply-to','')
        if in_reply_to_id:
            references.append(in_reply_to_id)
        tmp = []
        for ref in references:
            tmp.append(ref.replace("<", "").replace(">", ""))
        references = tmp
        logging.debug("Possible references in thread: %s"\
                      % ", ".join(references))
        in_reply_to = None
        for ref in references:
            try:
                in_reply_to = Mail.objects.get(
                    message_id=ref)
            except Mail.DoesNotExist:
                continue
        if not in_reply_to:
            # take all the emails that this user has initiated, and
            # find ones with the same subject.  sort them by date and
            # stick this in at the appropriate point.
            base_subject = strip_re(parsed_email['subject'])
            logging.debug("Trying subject heuristics")
            thread_starts = Mail.objects.filter(
                Q(mfrom=to_user,
                  in_reply_to=None,
                  subject__contains=base_subject) | \
                Q(mto=to_user,
                  in_reply_to=None,
                  subject__contains=base_subject))
            try:
                in_reply_to = thread_starts[0]
            except IndexError:
                pass
            
        if in_reply_to:
            name, mfrom = parseaddr(parsed_email['from'])
            mfrom, created = CustomUser.objects.get_or_create(email=mfrom)
            if created:
                if not in_reply_to.mto.organisation:
                    name = mfrom.email[mfrom.email.find('@')+1:]
                    in_reply_to.mto.organisation, _ = \
                               Organisation.objects.get_or_create(name=name)
                    in_reply_to.mto.save()
                mfrom.organisation = in_reply_to.mto.organisation
                mfrom.save()
            mto = to_user
            counter = 1
            for part in parsed_email.walk():
                if part.get_content_maintype() == "multipart":
                    continue # it's just a container
                filename = part.get_filename()
                counter += 1
                # XXX the following needs to change to save all parts
                # of a message
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
            logging.debug("Sending notification to %s, from %s" \
                          % (newmsg.mto.email, newmsg.mfrom.email))
            send_mail(mail=newmsg,
                      message=newmsg.message,
                      subject=newmsg.subject,
                      mfrom=newmsg.mfrom.email,                      
                      mto=newmsg.mto.email,
                      reply_to=newmsg.mfrom.proxy_email)
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
