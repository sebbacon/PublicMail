#!/usr/bin/env python
import string
import mimetypes
import os; os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
import sys
import email
from email.utils import parseaddr

from mail.models import Organisation
from mail.models import ProxyEmail
from mail.models import CustomUser
from mail.models import Mail
import settings

def get_charset(message, default="ascii"):
    """Get the message charset"""
    if message.get_content_charset():
        return message.get_content_charset()
    if message.get_charset():
        return message.get_charset()
    return default

def make_response_from_file(fp):
    parsed_email = email.message_from_file(fp)
    name, mto = parseaddr(parsed_email['to'])
    user = mto[:mto.find("@")]
    user = user.replace(settings.MAIL_PREFIX, "")
    try:
        proxy = ProxyEmail.objects.get(proxy_email=user)
        user = proxy.customuser_set.get()
        in_reply_to = None

        # http://www.jwz.org/doc/threading.html
        references = parsed_email.get('references','').split(" ")
        in_reply_to = parsed_email.get('in-reply-to','')
        if in_reply_to:
            references.append(in_reply_to)
        tmp = []
        for ref in references:
            tmp.append(ref.replace("<", "").replace(">", ""))
        message_id = parsed_email['message-id']\
                     .replace("<", "")\
                     .replace(">", "")
        references = tmp
        for ref in references:
            try:
                in_reply_to = Mail.objects.get(
                    message_id=ref)
            except Mail.DoesNotExist:
                continue
        if in_reply_to:
            name, mfrom = parseaddr(parsed_email['from'])
            mfrom, created = CustomUser.objects.get_or_create(email=mfrom)
            if created:
                if not in_reply_to.mto.organisation:
                    name = mfrom[mfrom.find('@')+1:]
                    in_reply_to.mto.organisation = \
                               Organisation.objects.create(name=name)
                    in_reply_to.mto.save()
                mfrom.organisation = mto.organisation.save()
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
    except ProxyEmail.DoesNotExist:
        print "couldn't find addressee"
        return False

if __name__ == "__main__":
    parsed_email = make_response_from_file(sys.stdin)
    if parsed_email:
        sys.exit(0)
    else:
        sys.exit(67) # addressee unknown

# Internal software error = 7-
