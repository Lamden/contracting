import abc

from redis import Redis
from seneca.config import DB_PORT, DB_URL, DB_DELIMITER, MASTER_DB, DB_TYPE
from seneca.exceptions import DatabaseDriverNotFound


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
    def xscan(self, *args, **kwargs):
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
    def __init__(self, host=DB_URL, port=DB_PORT, db=MASTER_DB, delimiter=DB_DELIMITER):
        self.conn = Redis(host=host, port=port, db=db)
        self.delimiter = delimiter
        self.connection_pool = self.conn.connection_pool

    def get(self, key):
        return self.conn.get(key)

    def set(self, key, value):
        self.conn.set(key, value)

    def delete(self, key):
        self.conn.delete(key)

    def keys(self, *args, **kwargs):
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
    cls = DATABASE_DRIVER_MAPS.get(DB_TYPE)
    if cls is None:
        raise DatabaseDriverNotFound(
            driver=DB_TYPE,
            known_drivers=DATABASE_DRIVER_MAPS.keys())
    return cls


DatabaseDriver = get_database_driver()


class ContractDriver(DatabaseDriver):
    def __init__(self, host=DB_URL, port=DB_PORT, delimiter=DB_DELIMITER, db=0, code_key='__code__',
                 type_key='__type__', author_key='__author__'):
        super().__init__(host=host, port=port, delimiter=delimiter, db=db)

        self.code_key = code_key
        self.type_key = type_key
        self.author_key = author_key

        # Tests if access to the DB is available
        self.conn.ping()

    def make_key(self, key, field):
        return '{}{}{}'.format(key, self.delimiter, field)

    def hget(self, key, field):
        return self.conn.get(
            self.make_key(key, field)
        )

    def hset(self, key, field, value):
        return self.conn.set(
            self.make_key(key, field),
            value=value
        )

    def get_contract(self, name):
        return self.hget(name, self.code_key)

    def push_contract(self, name, code, author, _type='user'):
        self.hset(name, self.code_key, code)
        self.hset(name, self.author_key, author)
        self.hset(name, self.type_key, _type)