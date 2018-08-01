#!/bin/bash
set -ex

cd /usr/local/mysql

su mysql -c 'bin/mysqld --console &'

echo "Waiting for mysqld to start..."
n=0
until [ $n -ge 15 ]
do
  ./bin/mysqladmin -h 127.0.0.1 version && break  # substitute your command here
  n=$[$n+1]
  echo "Still waiting..."
  sleep 3
done

./bin/mysql -h 127.0.0.1 -e "CREATE DATABASE $database /*\!40100 DEFAULT CHARACTER SET utf8 */;"
echo 'create db'
./bin/mysql -h 127.0.0.1 -e "CREATE USER $username@localhost IDENTIFIED BY '$password';"
echo 'create user'
./bin/mysql -h 127.0.0.1 -e "GRANT ALL ON *.* to $username@'%' IDENTIFIED BY '$password';"
./bin/mysql -h 127.0.0.1 -e "GRANT ALL ON *.* to $username@localhost IDENTIFIED BY '$password';"
echo 'grant privileges'
./bin/mysql -h 127.0.0.1 -e "FLUSH PRIVILEGES;"
echo 'Complete.'

echo 'Listening...'

while true; do
	sleep 5
done
