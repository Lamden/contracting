from rocks.client import RocksDBClient
from rocks import constants
from contracting.db.encoder import encode, decode, encode_kv
from contracting.execution.runtime import rt
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal
from datetime import datetime
import marshal
import decimal
# DB maps bytes to bytes
# Driver maps string to python object
CODE_KEY = '__code__'
TYPE_KEY = '__type__'
AUTHOR_KEY = '__author__'
OWNER_KEY = '__owner__'
TIME_KEY = '__submitted__'
COMPILED_KEY = '__compiled__'


# Probably want to put the runtime stuff here, tbh
class Driver:
    def __init__(self):
        self.db = RocksDBClient()

    def get(self, item: str):
        key = item.encode()
        # RT READ
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

        # RT SEEK
        self.db.seek(p)

        l = []
        k = None
        while k != constants.STOP_ITER_RESPONSE:
            # RT ITER
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


class InMemDriver(Driver):
    def __init__(self):
        super().__init__()
        self.db = {}

    def get(self, item):
        key = item.encode()
        value = self.db.get(key)
        return decode(value)

    def set(self, key: str, value):
        k = key.encode()
        if value is None:
            self.__delitem__(key)
        else:
            v = encode(value).encode()
            self.db[k] = v

    def delete(self, key: str):
        self.__delitem__(key)

    def iter(self, prefix: str, length=0):
        p = prefix.encode()

        l = []
        for k in sorted(self.db.keys()):
            if k.startswith(p):
                l.append(k.decode())
            if 0 < length <= len(l):
                break

        return l

    def keys(self):
        return sorted([k.decode() for k in self.db.keys()])

    def flush(self):
        self.db.clear()

    def __getitem__(self, item: str):
        value = self.get(item)
        if value is None:
            raise KeyError
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    def __delitem__(self, key: str):
        k = key.encode()
        try:
            del self.db[k]
        except KeyError:
            pass

class CacheDriver:
    def __init__(self, driver: Driver=Driver()):
        self.driver = driver
        self.cache = {}

        self.reads = set()
        self.pending_writes = {}

    def get(self, key: str, mark=True):
        # Try to get from cache
        v = self.cache.get(key)
        if v is not None:
            rt.deduct_read(*encode_kv(key, v))
            return v

        # If it doesn't exist, get from db, add to cache
        dv = self.driver.get(key)
        rt.deduct_read(*encode_kv(key, dv))

        self.cache[key] = dv

        # Add key to reads
        if mark:
            self.reads.add(key)

        return dv

    def set(self, key, value, mark=True):
        rt.deduct_write(*encode_kv(key, value))

        if type(value) == decimal.Decimal:
            value = ContractingDecimal(str(value))

        self.cache[key] = value
        if mark:
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

    def keys(self, prefix=''):
        return list(self.items(prefix).keys())

    def values(self, prefix=''):
        return list(self.items(prefix).values())

    def make_key(self, contract, variable, args=[]):
        contract_variable = self.delimiter.join((contract, variable))
        if args:
            return ':'.join((contract_variable, *args))
        return contract_variable

    def get_var(self, contract, variable, arguments=[], mark=True):
        key = self.make_key(contract, variable, arguments)
        return self.get(key, mark=mark)

    def set_var(self, contract, variable, arguments=[], value=None, mark=True):
        key = self.make_key(contract, variable, arguments)
        self.set(key, value, mark=mark)

    def get_contract(self, name):
        return self.get_var(name, CODE_KEY)

    def get_owner(self, name):
        return self.get_var(name, OWNER_KEY)

    def get_time_submitted(self, name):
        return self.get_var(name, TIME_KEY)

    def get_compiled(self, name):
        return self.get_var(name, COMPILED_KEY)

    def set_contract(self, name, code, owner=None, overwrite=False, timestamp=Datetime._from_datetime(datetime.now())):
        if self.get_contract(name) is None or overwrite:
            code_obj = compile(code, '', 'exec')
            code_blob = marshal.dumps(code_obj)

            self.set_var(name, CODE_KEY, value=code)
            self.set_var(name, COMPILED_KEY, value=code_blob)
            self.set_var(name, OWNER_KEY, value=owner)
            self.set_var(name, TIME_KEY, value=timestamp)

    def delete_contract(self, name):
        for key in self.keys(name):
            if self.cache.get(key) is not None:
                del self.cache[key]

            if self.pending_writes.get(key) is not None:
                del self.pending_writes[key]

            self.driver.delete(key)

    def flush(self):
        self.driver.flush()
        self.clear_pending_state()

    def get_contract_keys(self, name):
        return self.keys(name)

    def delete(self, key):
        if self.cache.get(key) is not None:
            del self.cache[key]

        if self.pending_writes.get(key) is not None:
            del self.pending_writes[key]

        self.driver.delete(key)