import abc

from redis import Redis
from .. import config
from ..exceptions import DatabaseDriverNotFound
from ..db.encoder import encode, decode

from ..logger import get_logger
from ..db.cr.conflict_resolution import CRContext
from ..db.cr.cr_commands import CRCmdGet, CRCmdSet

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

from redis.connection import Connection
# Lower level driver for added speed
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
DatabaseDriver = RedisConnectionDriver


class CacheDriver(DatabaseDriver):
    def __init__(self, host=config.DB_URL, port=config.DB_PORT, db=0,):
        super().__init__(host=host, port=port, db=db)
        self._reset()

    def _reset(self):
        self.modified_keys = defaultdict(deque)
        self.contract_modifications = list()
        self.new_tx()

    def get(self, key):
        key_location = self.modified_keys.get(key)
        if key_location is None:
            value = super().get(key)

        else:
            value = self.contract_modifications[key_location[-1]][key]
        return value

    def set(self, key, value):
        self.contract_modifications[-1].update({key: value})
        self.modified_keys[key].append(len(self.contract_modifications) - 1)

    def revert(self, idx=0):
        if idx == 0:
            self._reset()
        else:
            tmp = self.modified_keys.copy()
            for key, i in tmp.items():
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

        self._reset()

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


class CRDriver(DatabaseDriver):
    def __init__(self):
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.log = get_logger("CRDriver")
        self.working_db, self.master_db, self.contract_idx, self.cmds, self.cr_data = None, None, None, None, None
        self.cmds = None

    def setup(self, transaction_idx: int, cr_context: CRContext):
        self.cr_data = cr_context

        # why does this guy need a reference of working and master db? can we do away with that
        # update -- i think its for convenience so we dont have to do data.master_db ... seems silly though...
        self.working_db, self.master_db = cr_context.working_db, cr_context.master_db
        self.contract_idx = transaction_idx

        if self.cmds is None:
            self.cmds = {'get': CRCmdGet(self.working_db, self.master_db, self.contract_idx, self.cr_data),
                         'set': CRCmdSet(self.working_db, self.master_db, self.contract_idx, self.cr_data)}

    def get(self, key):
        cmd = self.cmds['get']
        cmd.set_params(working_db=self.working_db, master_db=self.master_db, contract_idx=self.contract_idx, data=self.cr_data)
        return cmd

    def set(self, key, value):
        cmd = self.cmds['set']
        cmd.set_params(working_db=self.working_db, master_db=self.master_db, contract_idx=self.contract_idx, data=self.cr_data)
        return cmd
