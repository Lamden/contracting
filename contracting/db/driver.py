import abc

from redis import Redis
from redis.connection import Connection
import plyvel
from .. import config
from ..exceptions import DatabaseDriverNotFound
from ..db.encoder import encode, decode

from ..logger import get_logger

from collections import deque, defaultdict
import marshal

class AbstractDatabaseDriver:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get(self, key):
        """Get the specified key from the database"""
        return

    @abc.abstractmethod
    def set(self, key, value):
        """Set the specified key in the database"""
        return

    @abc.abstractmethod
    def delete(self, key):
        """Delete the specified key from the Database"""
        return

    @abc.abstractmethod
    def flush(self, db):
        """Flush the selected database of all entries"""
        return

    @abc.abstractmethod
    def iter(self, prefix):
        return

    @abc.abstractmethod
    def keys(self):
        """Do a scan on the connection for all available keys"""
        return

    def exists(self, key):
        """Check whether a given key exists before attempting to query it"""
        if self.get(key) is not None:
            return True
        return False


# The theoretically fastest driver. It's a dictionary.
class DictDriver(AbstractDatabaseDriver):
    def __init__(self, **kwargs):
        self.conn = {}

    def get(self, key):
        return self.conn.get(key)

    def set(self, key, value):
        self.conn[key] = value

    def delete(self, key):
        del self.conn[key]

    def iter(self, prefix):
        keys = []
        for k, v in self.conn.items():
            if k.startswith(prefix):
                keys.append(k)
        return keys

    def keys(self):
        return self.conn.keys()

    def flush(self, db=None):
        del self.conn
        self.conn = {}

    def incrby(self, key, amount=1):
        """Increment a numeric key by one"""
        k = self.get(key)

        if k is None:
            k = 0
        k = int(k) + amount
        self.set(key, k)

        return k



class RedisConnectionDriver(AbstractDatabaseDriver):
    def __init__(self, host=config.DB_URL, port=config.DB_PORT, db=config.MASTER_DB):
        self.conn = Connection(host, port, db)

    def get(self, key):
        self.conn.send_command('GET', key)
        return self.conn.read_response()

    def set(self, key, value):
        self.conn.send_command('SET', key, value)
        self.conn.read_response()

    def delete(self, key):
        self.conn.send_command('DEL', key)
        self.conn.read_response()

    def iter(self, prefix):
        self.conn.send_command('KEYS', prefix+'*')
        return self.conn.read_response()

    def keys(self):
        return self.iter(prefix='')

    def flush(self, db=None):
        self.conn.send_command('FLUSHDB')
        self.conn.read_response()

    def incrby(self, key, amount=1):
        """Increment a numeric key by one"""
        k = self.get(key)

        if k is None:
            k = 0
        k = int(k) + amount
        self.set(key, k)

        return k




class RedisDriver(AbstractDatabaseDriver):
    def __init__(self, host=config.DB_URL, port=config.DB_PORT, db=config.MASTER_DB):
        self.conn = Redis(host=host, port=port, db=db)
        self.connection_pool = self.conn.connection_pool

    def get(self, key):
        return self.conn.get(key)

    def set(self, key, value):
        self.conn.set(key, value)

    def delete(self, key):
        self.conn.delete(key)

    def iter(self, prefix):
        return self.conn.scan_iter(match=prefix+'*')

    def keys(self):
        return self.conn.keys(pattern='*')

    def flush(self, db=None):
        self.conn.flushdb()

    def incrby(self, key, amount=1):
        """Increment a numeric key by one"""
        k = self.get(key)

        if k is None:
            k = 0
        k = int(k) + amount
        self.set(key, k)

        return k




GLOBAL_DB = plyvel.DB('state.db', create_if_missing=True, error_if_exists=False)


class LevelDBDriver(AbstractDatabaseDriver):
    def __init__(self, **kwargs):
        self.conn = GLOBAL_DB

    def get(self, key):
        try:
            key = key.encode()
        except AttributeError:
            pass

        return self.conn.get(key)

    def set(self, key, value):
        try:
            key = key.encode()
        except AttributeError:
            pass

        try:
            value = value.encode()
        except AttributeError:
            pass
        self.conn.put(key, value)

    def delete(self, key):
        try:
            key = key.encode()
        except AttributeError:
            pass

        self.conn.delete(key)

    def iter(self, prefix):
        try:
            prefix = prefix.encode()
        except AttributeError:
            pass
        it = self.conn.iterator(prefix=prefix)
        return [k[0] for k in it]

    def keys(self):
        return self.iter(prefix=b'')

    def flush(self, db=None):
        for k in self.keys():
            self.delete(k)

    def incrby(self, key, amount=1):
        """Increment a numeric key by one"""
        try:
            key = key.encode()
        except:
            pass

        k = self.conn.get(key)

        if k is None:
            k = 0
        k = int(k) + amount

        self.conn.put(key, '{}'.format(k).encode())

        return k



# Defined at the bottom since needs to be instantiated
# after the classes have been defined. Allows us to
# parameterize the type of database driver required
# from the top level instead of having to manually change
# a bunch of code to get to it.
DATABASE_DRIVER_MAPS = {
    'redis': RedisConnectionDriver,
    'leveldb': LevelDBDriver
}


def get_database_driver():
    cls = DATABASE_DRIVER_MAPS.get(config.DB_TYPE)
    if cls is None:
        raise DatabaseDriverNotFound(
            driver=config.DB_TYPE,
            known_drivers=DATABASE_DRIVER_MAPS.keys())
    return cls


DatabaseDriver = get_database_driver()
DatabaseDriver = LevelDBDriver


class CacheDriver(DatabaseDriver):
    def __init__(self, host=config.DB_URL, port=config.DB_PORT, db=0,):
        super().__init__(host=host, port=port, db=db)
        self.modified_keys = None
        self.contract_modifications = None
        self.original_values = None
        self.reset_cache()

    def reset_cache(self, modified_keys=None, contract_modifications=[], original_values={}):
        # Modified keys is a dictionary of deques representing the contracts that have modified
        # that key
        if modified_keys:
            self.modified_keys = modified_keys
        else:
            self.modified_keys = defaultdict(deque)
        # Contract modififications is a list of dicts containing the keys updated by a contract
        # and their final value
        self.contract_modifications = contract_modifications
        # Original values is a dictionary of keys representing the original value fetched from
        # the DB
        self.original_values = original_values
        # If we do not have any contract modifications, add a new one
        if len(self.contract_modifications) == 0:
            self.new_tx()

    def get(self, key):
        key_location = self.modified_keys.get(key)
        if key_location is None:
            value = super().get(key)
            self.original_values[key] = value
        else:
            value = self.contract_modifications[key_location[-1]][key]
        return value

    def set(self, key, value):
        self.contract_modifications[-1].update({key: value})
        # TODO: May have multiple instances of contract_idx if multiple sets on same key
        self.modified_keys[key].append(len(self.contract_modifications) - 1)

    def revert(self, idx=0):
        if idx == 0:
            self.reset_cache()
        else:
            for key, i in self.modified_keys.items():
                while len(i) >= 1:
                    if i[-1] >= idx:
                        i.pop()
                    else:
                        break
                if len(i) == 0:
                    i = None
                self.modified_keys[key] = i

            self.contract_modifications = self.contract_modifications[:idx + 1]

    def commit(self):
        for key, idx in self.modified_keys.items():
            super().set(key, self.contract_modifications[idx[-1]][key])

        self.reset_cache()

    def new_tx(self):
        self.contract_modifications.append(dict())


class ContractDriver(CacheDriver):
    def __init__(self, host=config.DB_URL, port=config.DB_PORT, delimiter=config.INDEX_SEPARATOR, db=0,
                 code_key=config.CODE_KEY, type_key=config.TYPE_KEY, author_key=config.AUTHOR_KEY):
        super().__init__(host=host, port=port, db=db)

        self.delimiter = delimiter

        self.code_key = code_key
        self.type_key = type_key
        self.author_key = author_key

        # Tests if access to the DB is available
        #self.conn.ping()

    def get(self, key):
        value = super().get(key)
        return decode(value)

    def set(self, key, value):
        v = encode(value)
        super().set(key, v)

    def make_key(self, key, field):
        return '{}{}{}'.format(key, self.delimiter, field)

    def hget(self, key, field):
        return self.get(
            self.make_key(key, field)
        )

    def hset(self, key, field, value):
        return self.set(
            self.make_key(key, field),
            value=value
        )

    def get_contract(self, name):
        return self.hget(name, self.code_key)

    def set_contract(self, name, code, author='sys', _type='user', overwrite=False):
        if not overwrite or self.is_contract(name):
            self.hset(name, self.code_key, code)
            self.hset(name, self.author_key, author)
            self.hset(name, self.type_key, _type)

            code_obj = compile(code, '', 'exec')
            code_blob = marshal.dumps(code_obj)
            self.hset(name, '__compiled__', code_blob)

    def get_compiled(self, name):
        return self.hget(name, '__compiled__')

    def delete_contract(self, name):
        for k in self.iter(prefix=name):
            self.delete(k)

    def is_contract(self, name):
        return self.exists(
            self.make_key(name, self.code_key)
        )

    def keys(self):
        return [k.decode() for k in super().keys()]

    def get_contract_keys(self, name):
        keys = [k.decode() for k in self.iter(prefix='{}{}'.format(name, self.delimiter))]
        return keys
