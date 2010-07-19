#!/usr/bin/env python
import string
import os; os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
import sys
import email
from email.utils import parseaddr

from mail.models import CustomUser
from mail.models import ProxyEmail
import settings

email = email.message_from_file(sys.stdin)

name, mto = parseaddr(email['to'])
user = mto[:mto.find("@")]
user = user.replace(settings.MAIL_PREFIX, "")
try:
    proxy = ProxyEmail.objects.get(proxy_email=user)
    user = proxy.customuser_set.get()
    print user
    print email.__dict__
except ProxyEmail.DoesNotExist:
    print "couldn't find addressee"
    sys.exit(67) # addressee unknown

# OK. 
sys.exit(0)

# Addressee unkown = 67
# Internal software error = 7-
