import os

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not args or (args and args[0] not in ('load')):
            raise CommandError("USAGE: ./manage.py %s load" % \
                    os.path.basename(__file__).split('.')[0])

        transaction.enter_transaction_management()
        transaction.managed(True)
        transaction.commit()
