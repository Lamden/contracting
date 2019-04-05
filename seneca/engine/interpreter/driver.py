from redis import Redis


class Driver:
    def __init__(self, host='localhost', port=6379, db=0, delimiter=':'):
        self.conn = Redis(host=host, port=port, db=db)
        self.delimiter = delimiter
        self.connection_pool = self.conn.connection_pool

    def get(self, key):
        return self.conn.get(key)

    def set(self, key, value):
        self.conn.set(key, value)

    def delete(self, key):
        self.conn.delete(key)

    def hget(self, field, key):
        return self.get('{}{}{}'.format(field, self.delimiter, key))

    def hset(self, field, key, value):
        self.set('{}{}{}'.format(field, self.delimiter, key), value)

    def hexists(self, *args, **kwargs):
        return bool(self.hget(*args, **kwargs))

    def hincrby(self, field, key, value):
        self.incr('{}{}{}'.format(field, self.delimiter, key), value)

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
