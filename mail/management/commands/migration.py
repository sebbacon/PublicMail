import os
import glob
import sys
from django.conf import settings
from django.db import connection, transaction
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = 'Gets the migration job done.'

    def handle_noargs(self, **options):
        cursor = connection.cursor()
        sql_files = glob.glob(os.path.join(settings.MIGRATIONS_ROOT, '*.sql'))
        py_files = glob.glob(os.path.join(settings.MIGRATIONS_ROOT, '*.py'))
        files = sorted(sql_files + py_files)
        alter_db = False
        for fn in files:
            done = '%s.done' % fn
            if not os.path.exists(done):
                if fn.endswith('sql'):
                    f = open(fn, 'r')
                    sql = f.read()
                    f.close()
                    print "Executing: %s" % os.path.split(fn)[1]
                    cursor.execute(sql)
                    transaction.commit_unless_managed()
                    alter_db = True
                else:
                    name, _ = os.path.splitext(os.path.split(fn)[1])
                    if name.startswith("__"):
                        continue
                    __import__('migrations', globals(), locals(), [name])
                    alter_db = sys.modules['migrations.%s' % name].main()
                open(done, 'w').close()

        if not alter_db:
            print "Up to date, nothing to do."
        else:
            print "Success!"
