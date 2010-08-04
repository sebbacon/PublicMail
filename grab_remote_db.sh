dropdb mailtrail
createdb mailtrail
ssh root@seb.fry-it.com 'su -c "pg_dump mailtrail " postgres' | psql mailtrail
