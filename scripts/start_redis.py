import os
import sys

if "DATADIR" in os.environ:
    DATA_DIR = os.environ["DATADIR"] + '/seneca'
else:
    DATA_DIR = '/var/db/seneca'

REDIS_CONF_PATH = '/etc/redis.conf'
REDIS_DIR = DATA_DIR + '/redis'


def start_redis(conf_path):
    print("Starting Redis server...")
    if not os.path.exists(REDIS_DIR):
        print("Creating Redis directory at {}".format(REDIS_DIR))
        os.makedirs(REDIS_DIR, exist_ok=True)

    print("Redis using data directory: {}".format(REDIS_DIR))

    if conf_path is not None:
        assert os.path.exists(conf_path), "No redis.conf file found at path {}".format(conf_path)
        os.system('redis-server {}'.format(conf_path))
    else:
        os.system('redis-server')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '-no-conf':
            start_redis(None)
        else:
            start_redis(sys.argv[1])
    else:
        start_redis(REDIS_CONF_PATH)

