import os
import random

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.contrib.auth.models import get_hexdigest

from mail.models import CustomUser

def get_hash(self, raw_password):
    algo = 'sha1'
    salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
    hsh = get_hexdigest(algo, salt, raw_password)
    password = '%s$%s$%s' % (algo, salt, hsh)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not args or (args and args[0] not in ('newuser')):
            raise CommandError("USAGE: ./manage.py %s username password" % \
                    os.path.basename(__file__).split('.')[0])

        transaction.enter_transaction_management()
        transaction.managed(True)
        
        username = args[1]
        password = args[2]

        user = CustomUser(username=username)
        user.set_password(password)
        user.save()
        
        
        transaction.commit()

