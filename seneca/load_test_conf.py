import os
import configparser
import MySQLdb

settings = configparser.ConfigParser()
settings._interpolation = configparser.ExtendedInterpolation()
this_dir = os.path.dirname(__file__)
db_conf_path = os.path.join(this_dir, '../test_db_conf.ini')

settings.read(db_conf_path)

db_settings = { 'username': settings.get('DB', 'username'),
  'password': settings.get('DB', 'password'),
  'db': settings.get('DB', 'database'),
  'host': settings.get('DB', 'hostname')
}


def get_mysql_conn():
    return MySQLdb.connect(host=db_settings['host'],
                           user=db_settings['username'],
                           passwd=db_settings['password'],
                           port=3306,
                           connect_timeout=5)
