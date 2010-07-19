dropdb volnet
createdb volnet
ssh seb.fry-it.com 'su -c "pg_dump volnet " postgres' | psql volnet
