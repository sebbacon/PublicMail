import hashlib
import itertools

from django.db import models
from django.contrib.auth.models import User, UserManager
from django.db.models import permalink
from django.contrib.sites.models import Site

import settings

class Organisation(models.Model):
    name = models.CharField(max_length=120,
                            unique=True)

class CustomUser(User):
    proxy_email_id = models.CharField(max_length=10)
    organisation = models.ForeignKey(Organisation,
                                     blank=True,
                                     null=True)
    needs_moderation = models.BooleanField(default=True)
    
    objects = UserManager()

    def __init__(self, *args, **kwargs):
        """Automatically generate a unique email user portion
        """
        try:
            email = kwargs['email']
            super(CustomUser, self).__init__(*args, **kwargs)
            proxy_email_id = None
            n = 0
            while not proxy_email_id:
                h = hashlib.sha256(email)
                attempt = h.hexdigest()[n:n+6]
                try:
                    already_got = CustomUser.objects.get(
                        proxy_email_id=attempt)
                    n += 1
                except CustomUser.DoesNotExist:
                    proxy_email_id = attempt
            self.proxy_email_id = proxy_email_id
        except KeyError:
            super(CustomUser, self).__init__(*args, **kwargs)
        
    @property
    def proxy_email(self):
        return "%s%s@%s" % (settings.MAIL_PREFIX,
                            self.proxy_email_id,
                            settings.MAIL_DOMAIN)

    @property
    def display_name(self):
        if self.first_name:
            name = self.first_name
        else:
            name = self.email
        return name
    
        
    def __unicode__(self):
        return "%s (%s)" % (self.email, self.proxy_email)

    @permalink
    def get_absolute_url(self):
        return ("user", (self.id,))


def _make_message_id(message):
    return "%s%s-%s" % (message.mfrom.proxy_email,
                        message.id,
                        Site.objects.get_current().domain)

class Mail(models.Model):
    subject = models.CharField(max_length=120)
    mfrom = models.ForeignKey(CustomUser,
                              related_name="mfrom")
    mto = models.ForeignKey(CustomUser,
                            related_name="mto")
    message = models.TextField()
    in_reply_to = models.ForeignKey('self',
                                    related_name="replies",
                                    blank=True,
                                    null=True)
    previewed = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    sent = models.DateTimeField(blank=True,
                                null=True)
    message_id = models.CharField(max_length=50)
    
    @permalink
    def get_absolute_url(self):
        return ("mail", (self.id,))

    def __unicode__(self):
        reply_to_msgid = self.in_reply_to \
                         and self.in_reply_to.message_id
        return "%s <%s> in reply to <%s>" % (self.subject,
                                             self.message_id,
                                             reply_to_msgid)

    def childwalk(self):
        for child in self.replies.all():
            if child.replies.count():
                for subchild in child.childwalk():
                    yield subchild
            else:
                yield child

    def ordered_childwalk(self):
        thread = list(self.childwalk())
        thread.sort(lambda x,y: cmp(x.created, y.created))
        return thread
    
    def all_in_thread(self):
        node = self.start_of_thread()
        return itertools.chain([node], node.ordered_childwalk())
    
    def start_of_thread(self):
        node = self
        parent = node
        while True:
            parent = node.in_reply_to
            if not parent:
                break
            node = parent
        return node

    def end_of_thread(self):
        if self.replies.count():
            thread = self.ordered_childwalk()
            return thread[-1]
        else:
            return self
        
    def save(self, *args, **kwargs):
        self.message_id = _make_message_id(self)
        super(Mail, self).save(*args, **kwargs)

