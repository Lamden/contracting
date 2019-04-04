from walrus.tusks.ledisdb import WalrusLedis
from walrus import Walrus
from redis import Redis

# class Driver(WalrusLedis):
#     """
#     Connects to the Walrus ORM with Ledis as back-end. We will only allow items that use sets because
#     conflict resolution currently does not support
#     """


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

class ConcurrentDriver(Redis):

    def hget(self, hash_key, key):
        return self.get(hash_key+':'+key)

    def hset(self, hash_key, key, value):
        return self.set(hash_key+':'+key, value)

    def hexists(self, *args, **kwargs):
        return bool(self.hget(*args, **kwargs))

    def hincrby(self, hash_key, key, value):
        res = self.hget(hash_key, key)
        self.hset(hash_key, key, int(res)+value)

    def hmget(self, hash_key, keys):
        res = []
        for key in keys:
            r = self.hget(hash_key, key)
            if r: res.append(r)
        return res

    def hmset(self, hash_key, objs):
        for key, obj in objs.items():
            self.hset(hash_key, key, obj)

    # def keys(self):
    #     keys_count, keys = self.scan_generic('SCAN')
    #     return keys

    def xscan(self, *args, **kwargs):
        return self.keys(pattern='*')

    # def __getattribute__(self, name):
    #     print("CONCURRENT DRIVER RETURNING ATTR {}".format(name))
    #     return object.__getattribute__(self, name)


class Driver(ConcurrentDriver):
    """
    Connects to the Walrus ORM with Ledis as back-end. We will only allow items that use sets because
    conflict resolution currently does not support
    """

    def __init__(self, *args, **kwargs):
        kwargs['port'] = 6379
        super().__init__(*args, **kwargs)