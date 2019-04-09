import abc

from redis import Redis
from seneca.config import DB_PORT, DB_URL, DB_DELIMITER, MASTER_DB


class AbstractDriver:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get(self, key):
        return

    @abc.abstractmethod
    def set(self, key, value):
        return

    @abc.abstractmethod
    def delete(self, key):
        return

    @abc.abstractmethod
    def flush(self, db):
        return

    @abc.abstractmethod
    def iter(self, prefix):
        return


class Driver:
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

    def incrby(self, key, amount=1):
        k = self.get(key)

        if k is None:
            k = 0
        k = int(k) + amount
        self.set(key, k)

        return k

    def flush(self, db=None):
        self.conn.flushdb()

    def xscan(self, *args, **kwargs):
        return self.conn.keys(pattern='*')

    def exists(self, key):
        if self.get(key) is not None:
            return True
        return False
