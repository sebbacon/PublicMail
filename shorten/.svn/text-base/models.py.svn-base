import hashlib

from django.db import models
from django.contrib.sites.models import Site

from django.core.urlresolvers import reverse

class ShortenedManager(models.Manager):
    def _key_gen(self, t):
        return hashlib.sha1(t).hexdigest()[:7]

    def make(self, url, description):
        key = self._key_gen(url + description)

        try:
            short = Shortened.objects.get(key=key)
        except Shortened.DoesNotExist:           
            short = Shortened.objects.create(url=url,
                                             description=description,
                                             key=key)

        current_site = Site.objects.get_current()

        return "http://%s%s" % (current_site.domain,
                                reverse('shorten', kwargs={'key': key}))

class Shortened(models.Model):
    key = models.CharField(max_length=50)
    description = models.TextField()
    url = models.CharField(max_length=2048)
    count = models.IntegerField(default=0)
    
    objects = ShortenedManager()

    def __unicode__(self):
        return "%s for %s" % (self.url, self.description)

    class Meta:
        verbose_name_plural = "Shortened urls"
