import random, seneca
from os import getenv as env
from dotenv import load_dotenv

path = seneca.__path__[0]
load_dotenv(dotenv_path='{}/../docker/redis.env'.format(path))

REDIS_PORT = env('REDIS_PORT', 6379)
REDIS_PASSWORD = env('REDIS_PASSWORD', '')
MASTER_DB = 0
DB_OFFSET = 1
