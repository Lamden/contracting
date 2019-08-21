import abc

# we can't include pylevel in production since its not installed on the docker images and will
# result in an interpret time error
from redis import Redis
from redis.connection import Connection
from ..db.encoder import encode, decode

from ..execution.runtime import rt

from .. import config

import marshal


class AbstractDatabaseDriver:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __getstate__(self):
        """Remove unpicklable objects (i.e. conn)"""
        return

    @abc.abstractmethod
    def __setstate__(self, state):
        """Re-add unpicklable objects (i.e. conn)"""
        return

    @abc.abstractmethod
    def get(self, key):
        """Get the specified _key from the database"""
        return

    @abc.abstractmethod
    def set(self, key, value):
        """Set the specified _key in the database"""
        return

    @abc.abstractmethod
    def delete(self, key):
        """Delete the specified _key from the Database"""
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
        """Check whether a given _key exists before attempting to query it"""
        if self.get(key) is not None:
            return True
        return False


class RedisConnectionDriver(AbstractDatabaseDriver):
    def __init__(self, host=config.DB_URL, port=config.DB_PORT, db=config.MASTER_DB):
        self.host = host
        self.db = db
        self.port = port
        self.conn = None
        self._setup_conn()

    def _setup_conn(self):
        self.conn = Connection(self.host, self.port, self.db)

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['conn']
        return state

    def __setstate__(self, state):
        for k,v in state.items():
            setattr(self, k, v)
        self._setup_conn()

    def get(self, key):
        self.conn.send_command('GET', key)
        resp = self.conn.read_response()
        return resp

    def set(self, key, value):
        self.conn.send_command('SET', key, value)
        resp = self.conn.read_response()

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
        """Increment a numeric _key by one"""
        return self.conn.send_command('INCRBY', key, amount)


class RedisDriver(AbstractDatabaseDriver):
    def __init__(self, host=config.DB_URL, port=config.DB_PORT, db=config.MASTER_DB):
        self.host = host
        self.port = port
        self.db = db
        self.conn = None
        self.connection_pool = None
        self._setup_conn()

    def _setup_conn(self):
        self.conn = Redis(host=self.host, port=self.port, db=self.db)
        self.connection_pool = self.conn.connection_pool

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['conn']
        del state['connection_pool']
        return state

    def __setstate__(self, state):
        for k, v in state.items():
            setattr(self, k, v)
        self._setup_conn()

    def get(self, key):
        val = self.conn.get(key)

        if val is not None and rt.tracer.is_started():
            cost = len(key) + len(val)
            cost *= config.READ_COST_PER_BYTE
            rt.tracer.add_cost(cost)

        return val

    def set(self, key, value):

        if rt.tracer.is_started():
            cost = len(key) + len(value)
            cost *= config.READ_COST_PER_BYTE
            rt.tracer.add_cost(cost)

        self.conn.set(key, value)

    def delete(self, key):
        self.conn.delete(key)

    def iter(self, prefix):
        return list(self.conn.scan_iter(match=prefix+'*'))

    def keys(self):
        return self.conn.keys(pattern='*')

    def flush(self, db=None):
        self.conn.flushdb()

    def incrby(self, key, amount=1):
        """Increment a numeric _key by one"""
        return self.conn.incrby(key, amount)


class ContractDriver(RedisConnectionDriver):
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

    def values(self, prefix):
        keys = super().iter(prefix=prefix)
        values = []
        for key in keys:
            value = self.get(key)
            values.append(value)
        return values

    def items(self, prefix):
        keys = self.iter(prefix=prefix)
        kvs = []
        for key in keys:
            value = self.get(key)
            kvs.append((key, value))
        return kvs

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
