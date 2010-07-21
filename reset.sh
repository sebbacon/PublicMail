dropdb mailtrail
createdb -O seb mailtrail
rm -rf mail/migrations/*
./manage.py startmigration mail --initial
./manage.py syncdb
./manage.py migrate
