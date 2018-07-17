#!/bin/bash
eval $(./scripts/source_flat_ini.py test_db_conf.ini)
echo "$username $password $database"
docker run -dp 3306:3306 seneca-myrocks-test ${username} ${password} ${database}
docker ps
