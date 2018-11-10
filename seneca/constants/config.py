import random, seneca
from os import getenv as env
from dotenv import load_dotenv

def load_env():
    load_dotenv(dotenv_path='{}/../docker/redis.env'.format(path), override=True)

def get_redis_port():
    if env('CIRCLECI'):
        return 6379
    return env('REDIS_PORT', 6379)

def get_redis_password():
    if env('CIRCLECI'):
        return ''
    return env('REDIS_PASSWORD', '')

path = seneca.__path__[0]
load_env()

MASTER_DB = 0
DB_OFFSET = 1
NUM_CACHES = 2
CODE_OBJ_MAX_CACHE = 64
