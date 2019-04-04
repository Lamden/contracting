from redis import Redis


class RawDriver:
    def get(self, key):
        raise NotImplementedError

    def set(self, key, value):
        raise NotImplementedError


class RedisLikeDriver(RawDriver):
    def hget(self, field, key):
        raise NotImplementedError

    def hset(self, field, key, value):
        raise NotImplementedError

    def hexists(self, *args, **kwargs):
        raise NotImplementedError

    def hincrby(self, field, key, value):
        raise NotImplementedError


class Driver(RedisLikeDriver):
    def __init__(self, host='localhost', port=6379, db=0, delimiter=':'):
        self.conn = Redis(host=host, port=port, db=db)
        self.delimiter = delimiter
        self.connection_pool = self.conn.connection_pool

    def get(self, key):
        return self.conn.get(key)

    def set(self, key, value):
        self.conn.set(key, value)

    def hget(self, field, key):
        return self.get('{}{}{}'.format(field, self.delimiter, key))

    def hset(self, field, key, value):
        self.set('{}{}{}'.format(field, self.delimiter, key), value)

    def hexists(self, *args, **kwargs):
        return bool(self.hget(*args, **kwargs))

    def hincrby(self, field, key, value):
        res = self.hget(field, key)
        self.hset(field, key, int(res) + value)

    def hmget(self, field, keys):
        res = []
        for key in keys:
            r = self.hget(field, key)
            if r: res.append(r)
        return res

    def hmset(self, field, mapping):
        for key, val in mapping.items():
            self.hset(field, key, val)

    def xscan(self, *args, **kwargs):
        return self.conn.keys(pattern='*')

    def flushall(self):
        self.conn.flushall()

    def flushdb(self):
        self.conn.flushdb()

    def hlen(self, field, key):
        self.conn.hlen('{}{}{}'.format(field, self.delimiter, key))

    def delete(self, key):
        self.conn.delete(key)

    def exists(self, key):
        if self.get(key) is not None:
            return True
        return False

    def incr(self, key, amount=1):
        k = self.get(key)

        if k is None:
            k = 0
        k = int(k) + amount
        self.set(key, k)

        return k
