eval $(./scripts/source_flat_ini.py test_db_conf.ini)
mysql -h 127.0.0.1 -u ${username} --password=${password} --database=${database}
