import hashlib

from django.db import models
from django.contrib.auth.models import User, UserManager
from django.db.models import permalink


class ProxyEmail(models.Model):
    def __init__(self, *args, **kwargs):
        """Automatically generate a unique email user portion
        """
        try:
            email = kwargs.pop('email')
            super(ProxyEmail, self).__init__(*args, **kwargs)
            proxy_email = None
            n = 0
            while not proxy_email:
                h = hashlib.sha256(email)
                attempt = h.hexdigest()[n:n+6]
                try:
                    already_got = ProxyEmail.objects.get(
                        proxy_email=attempt)
                    n += 1
                except ProxyEmail.DoesNotExist:
                    proxy_email = attempt
            self.proxy_email = proxy_email
        except KeyError:
            super(ProxyEmail, self).__init__(*args, **kwargs)
        
    proxy_email = models.CharField(primary_key=True,
                                   max_length=10)

    def __unicode__(self):
        return self.proxy_email

class CustomUser(User):
    proxy_email = models.ForeignKey(ProxyEmail)
    needs_moderation = models.BooleanField(default=True)
    
    objects = UserManager()

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

    def save(self, *args, **kwargs):
        self.proxy_email = ProxyEmail.objects.create(
            email=self.email)
        super(CustomUser, self).save(*args, **kwargs)


class Organisation(models.Model):
    name = models.CharField(max_length=120,
                            unique=True)

class Recipient(models.Model):
    email = models.EmailField(primary_key=True)
    organisation = models.ForeignKey(Organisation,
                                     blank=True,
                                     null=True)

class Mail(models.Model):
    subject = models.CharField(max_length=120)
    mfrom = models.ForeignKey(CustomUser)
    mto = models.ForeignKey(Recipient)
    message = models.TextField()
    in_reply_to = models.OneToOneField('self',
                                       blank=True,
                                       null=True)
    previewed = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    sent = models.DateTimeField(blank=True,
                                null=True)

    @permalink
    def get_absolute_url(self):
        return ("mail", (self.id,))

    def next_in_thread(self):
        try:
            yield Mail.objects.get(in_reply_to=self)
        except Mail.DoesNotExist:
            pass
