import abc

from redis import Redis
from seneca import config
from seneca.exceptions import DatabaseDriverNotFound
from seneca.db.encoder import encode, decode

from seneca.logger import get_logger

from collections import deque, defaultdict


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



# Defined at the bottom since needs to be instantiated
# after the classes have been defined. Allows us to
# parameterize the type of database driver required
# from the top level instead of having to manually change
# a bunch of code to get to it.
DATABASE_DRIVER_MAPS = {
    'redis': RedisDriver
}


def get_database_driver():
    cls = DATABASE_DRIVER_MAPS.get(config.DB_TYPE)
    if cls is None:
        raise DatabaseDriverNotFound(
            driver=config.DB_TYPE,
            known_drivers=DATABASE_DRIVER_MAPS.keys())
    return cls


DatabaseDriver = get_database_driver()


class CacheDriver(DatabaseDriver):
    def __init__(self, host=config.DB_URL, port=config.DB_PORT, db=0,):
        super().__init__(host=host, port=port, db=db)
        self.modified_keys = None
        self.contract_modifications = None
        self.original_values = None
        self.reset_cache()

    def reset_cache(self, modified_keys=None, contract_modifications=None, original_values={}):
        # Modified keys is a dictionary of deques representing the contracts that have modified
        # that key
        if self.modified_keys:
            self.modified_keys = modified_keys
        else:
            self.modified_keys = defaultdict(deque)
        # Contract modififications is a list of dicts containing the keys updated by a contract
        # and their final value
        if self.contract_modifications:
            self.contract_modifications = contract_modifications
        else:
            self.contract_modifications = list()
        # Original values is a dictionary of keys representing the original value fetched from
        # the DB
        self.original_values = original_values
        # If we do not have any contract modifications, add a new one
        if len(contract_modifications) == 0:
            self.new_tx()

    def get(self, key):
        key_location = self.modified_keys.get(key)
        if key_location is None:
            value = self.conn.get(key)
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
            self.conn.set(key, self.contract_modifications[idx[-1]][key])

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
        self.conn.ping()

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

    def delete_contract(self, name):
        for k in self.iter(prefix=name):
            self.delete(k)

    def is_contract(self, name):
        return self.exists(
            self.make_key(name, self.code_key)
        )

    def get_contract_keys(self, name):
        keys = [k.decode() for k in self.iter(prefix='{}{}'.format(name, self.delimiter))]
        return keys

