# keeps a running count of variables to calculate their keys where key =
# contract_name
import hashlib
import redis
from seneca.constants.config import get_redis_port, MASTER_DB, DB_OFFSET, get_redis_password
from seneca.engine.interpreter import SenecaInterpreter
from seneca.engine.conflict_resolution import RedisProxy
from seneca.engine.book_keeper import BookKeeper


REDIS_PORT = get_redis_port()
REDIS_PASSWORD = get_redis_password()


class Registry:
    mapping = {}
    count = 0

    @classmethod
    def add(cls, obj):
        cls.mapping[obj] = cls.count
        cls.count += 1

    @classmethod
    def get_key(cls, obj):
        idx = cls.mapping[obj]

        try:
            contract_id = SenecaInterpreter.loaded['__main__']['rt']['contract']
        except:
            contract_id = ''

        sha3 = hashlib.sha3_256()
        sha3.update(contract_id.encode())
        contract_hash = sha3.digest()

        sha3 = hashlib.sha3_256()
        sha3.update(contract_hash)

        hex_string = hex(idx)[2:]

        # pad hex if string is odd. otherwise it won't convert into bytes
        if len(hex_string) % 2 == 1:
            hex_string = '0' + hex_string

        sha3.update(bytes.fromhex(hex_string))
        return sha3.digest()

    @classmethod
    def flush(cls):
        cls.mapping.clear()
        cls.count = 0


class Data:
    def __init__(self, use_local=False):
        Registry.add(self)
        self.key = Registry.get_key(self)
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
        self.driver.get(self.key)


class Int(Data):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set(self, d):
        assert isinstance(d, int), 'Provided argument is not an integer.'
        super().set(d)


class Str(Data):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set(self, d):
        assert isinstance(d, int), 'Provided argument is not a string.'
        super().set(d)


class Bool(Data):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set(self, d):
        assert isinstance(d, bool), 'Provided argument is not a boolean.'
        super().set(d)


class Bytes(Data):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set(self, d):
        assert isinstance(d, bytes), 'Provided argument is not a byte string.'
        super().set(d)

# p(<key>) is the value. you set it to a key (which has to be automatic) and 'getting' it will return
class Pointer(Data):
    pass

# if self.key > 32, pop the first byte and analyze it
# if l, its a list at key [1:]
# if m, map
# if r, ranking

class List(Data):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set(self, i, v):
        self.driver.lset(self.key, i, v)

    def append(self, v):
        self.driver.rpush(self.key, v)

    def extend(self, l):
        for e in l:
            self.append(e)

    def push(self, v):
        self.driver.lpush(self.key, v)

    def pop(self):
        return self.driver.lpop(self.key)

    def pop_right(self):
        return self.driver.rpop(self.key)


class Map(Data):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set(self, k, v):
        self.driver.hmset(self.key, {k: v})

    def get(self, k):
        self.driver.hmget(self.key, k)


class Ranking:
    pass