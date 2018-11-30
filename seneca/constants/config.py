import random, seneca
from os import getenv as env
from dotenv import load_dotenv


def load_env():
    load_dotenv(dotenv_path='{}/../docker/redis.env'.format(path), override=True)


def get_redis_port(port=None):
    if port is not None:
        return port

    if env('CIRCLECI'):
        return 6379

    return env('REDIS_PORT', 6379)


def get_redis_password(password=None):
    if password is not None:
        return password

    if env('CIRCLECI'):
        return ''

    return env('REDIS_PASSWORD', '')

path = seneca.__path__[0]
load_env()

MASTER_DB = 0
DB_OFFSET = 1
CODE_OBJ_MAX_CACHE = 64

# Number of available db's SenecaClients have available to get ahead on the next sub block while other sb's are
# awaiting a merge confirmation
NUM_CACHES = 2

# Number of sb's to queue up if we run out of caches
MAX_SB_QUEUE_SIZE = 8
