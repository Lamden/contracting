#!/bin/bash

set -e

cd /usr/local/mysql

su mysql -c 'bin/mysqld --console &'

echo "Waiting for mysqld to start..."
sleep 5 &&

./bin/mysql -e "CREATE DATABASE $3 /*\!40100 DEFAULT CHARACTER SET utf8 */;"
echo 'create db'
./bin/mysql -e "CREATE USER $1@localhost IDENTIFIED BY '$2';"
echo 'create user'
./bin/mysql -e "GRANT ALL ON *.* to $1@'%' IDENTIFIED BY '$2';"
echo 'grant privileges'
./bin/mysql -e "FLUSH PRIVILEGES;"
echo 'Complete.'

echo 'Listening...'

while true; do
	sleep 5
done
