# Registry gives keys based on a list

# keeps a running count of variables to calculate their keys where key =
# contract_name
import hashlib
import secrets
import redis
from seneca.constants.config import get_redis_port, MASTER_DB, DB_OFFSET, get_redis_password
from seneca.engine.interpreter import SenecaInterpreter
from seneca.engine.conflict_resolution import RedisProxy
from seneca.engine.book_keeper import BookKeeper

REDIS_PORT = get_redis_port()
REDIS_PASSWORD = get_redis_password()

def resolve(key, driver):
    driver = redis.StrictRedis(host='localhost', port=REDIS_PORT, db=MASTER_DB, password=REDIS_PASSWORD)
    t = driver.type(key)


class Registry:
    # Maps objects to a count for lookup
    count = 0


class Data:
    def __init__(self, use_local=False, register=True, key=None):
        Registry.add(self)
        self.prefix = 'd'
        if register:
            self.key = Registry.get_key(self)
        else:
            self.key = key
        self.concurrent_mode = SenecaInterpreter.concurrent_mode
        if self.concurrent_mode and not use_local:
            assert BookKeeper.has_info(), "No BookKeeping info found for this thread/process with key {}. Was set_info " \
                                          "called on this thread first?".format(BookKeeper._get_key())
            info = BookKeeper.get_info()
            self.driver = RedisProxy(sbb_idx=info['sbb_idx'], contract_idx=info['contract_idx'], data=info['data'])
        else:
            self.driver = redis.StrictRedis(host='localhost', port=REDIS_PORT, db=MASTER_DB, password=REDIS_PASSWORD)

    def set(self, *args):
        self.driver.set(self.key, args[0])

    def get(self, *args):
        return self.driver.get(self.key)