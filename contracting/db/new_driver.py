from rocks.client import RocksDBClient
from rocks import constants
from contracting.db.encoder import encode, decode
from contracting.execution.runtime import rt

# DB maps bytes to bytes
# Driver maps string to python object
CODE_KEY = '__code__'
TYPE_KEY = '__type__'
AUTHOR_KEY = '__author__'
OWNER_KEY = '__owner__'
TIME_KEY = '__submitted__'


class Driver:
    def __init__(self):
        self.db = RocksDBClient()

    def get(self, item: str):
        key = item.encode()
        value = self.db.get(key)
        return decode(value)

    def set(self, key: str, value):
        k = key.encode()
        if value is None:
            self.__delitem__(key)
        else:
            v = encode(value).encode()
            self.db.set(k, v)

    def delete(self, key: str):
        self.__delitem__(key)

    def iter(self, prefix: str, length=0):
        p = prefix.encode()

        self.db.seek(p)

        l = []
        k = None
        while k != constants.STOP_ITER_RESPONSE:
            k = self.db.next()
            if not k.startswith(p):
                break
            if k != constants.STOP_ITER_RESPONSE:
                # Appends the decoded KEY. Not the value.
                l.append(k.decode())
            if 0 < length <= len(l):
                break

        return l

    def keys(self):
        return self.iter('')

    def flush(self):
        self.db.flush()

    def __getitem__(self, item: str):
        value = self.get(item)
        if value is None:
            raise KeyError
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    def __delitem__(self, key: str):
        k = key.encode()
        self.db.delete(k)


class CacheDriver:
    def __init__(self, driver: Driver):
        self.driver = driver
        self.cache = {}

        self.reads = set()
        self.pending_writes = {}

    def get(self, key: str):
        # Try to get from cache
        v = self.cache.get(key)
        if v is not None:
            rt.deduct_read(key, v)
            return v

        # If it doesn't exist, get from db, add to cache
        dv = self.driver.get(key)
        rt.deduct_read(key, dv)

        self.cache[key] = dv

        # Add key to reads
        self.reads.add(key)

        return dv

    def set(self, key, value):
        rt.deduct_write(key, value)
        self.cache[key] = value
        self.pending_writes[key] = value

    def commit(self):
        for k, v in self.pending_writes.items():
            self.driver.set(k, v)

    def clear_pending_state(self):
        self.cache.clear()
        self.reads.clear()
        self.pending_writes.clear()


class ContractDriver(CacheDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delimiter = '.'

    def items(self, prefix=''):
        # Get all of the items in the cache currently
        _items = {}
        keys = set()
        for k, v in self.cache.items():
            if k.startswith(prefix):
                _items[k] = v
                keys.add(k)

        # Get all of the keys we need
        db_keys = set(self.driver.iter(prefix=prefix))

        # Subtract the already gotten keys
        for k in db_keys - keys:
            _items[k] = self.get(k) # Cache get will add the keys to the cache

        return _items

    def values(self, prefix=''):
        return list(self.items(prefix).values())

    def make_key(self, contract, variable, args=[]):
        contract_variable = self.delimiter.join((contract, variable))
        if args:
            return ':'.join((contract_variable, *args))
        return contract_variable

    def get_var(self, contract, variable, arguments=[]):
        key = self.make_key(contract, variable, arguments)
        return self.get(key)

    def set_var(self, contract, variable, arguments=[], value=None):
        key = self.make_key(contract, variable, arguments)
        self.set(key, value)

    def get_contract(self, name):
        return self.get_var(name, CODE_KEY)

    def get_owner(self, name):
        return self.get_var(name, OWNER_KEY)

    def get_time_submitted(self, name):
        return self.get_var(name, TIME_KEY)