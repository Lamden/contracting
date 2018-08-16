import redis as rr
from seneca.engine.storage.resp_commands import *

class Transaction:
    def __init__(self, transaction_group):
        self._pending_changes = {} # dict of keys, figure out how this words with mset
        self._transaction_group = transaction_group6
        self._is_soft_commited = False
        self._revision = 0
        self._write_only_revision = 0

    def _do_type_check(self, key):
        raise NotImplementedError()

    def _do_read(self, key):
        raise NotImplementedError()

    def run_command(self, command):
        assert issubclass(type(command), Command)

        if issubclass(type(command), WriteCommand):
            self._write_only_revision +=1
            pass

        if issubclass(type(command), TypeDependantWriteCommand):
            pass


        self._revision += 1
        # * lookup key in self.pending_changes
        #   * If exists, merge
        #   * If not, write
        # Will have to run typecheck on some commands
        # self._revision += 1
        #TypeDependantWriteCommand
        # if write command self._write_only_revision += 0
        raise NotImplementedError()

    def soft_commit(self):
        if self._transaction_group:
            # get downstream committed transactions (if there are any)
            # check for read dependencies in those transactions against writes in this one.
            raise NotImplementedError()
            # self._is_soft_commited = True

        self._is_soft_commited = True
        return True

    def get_soft_committed(self):
        return self._is_soft_commited

    def clear(self):
        if self._transaction_group:
            raise NotImplementedError()

        self._pending_changes = {}


class TransactionGroup:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()
        self.executer = rr.StrictRedis(*args, **kwargs)
        self.save_points = []

    def append_new_transaction(self):
        return self.insert_new_transaction(len(self.save_points))

    def insert_new_transaction(self, index):
        sp = SavePoint(self)
        self.save_points.index(indesx, sp)
        return sp

    def get_upstream(self, transaction):
        raise NotImplementedError()

    def get_upstream(self, transaction):
        raise NotImplementedError()

    def write_out(self):
        # TODO: optimize by compacting transactions before sending
        # TODO: commit to Redis
        raise NotImplementedError()


# r = redis.Redis(
#     host='hostname',
#     port=port,
#     password='password')
#r.set('foo', 'bar')
#r.get('foo')
#By default, all responses are returned as bytes in Python 3


# def incrby(self, name, amount=1):
#        """
#        Increments the value of ``key`` by ``amount``.  If no key exists,
#        the value will be initialized as ``amount``
#        """
#
#        # An alias for ``incr()``, because it is already implemented
#        # as INCRBY redis command.
#        return self.incr(name, amount)
#







'''
## We won't implment ##
* Pipelines
  * They're a subclass redis base,
  * pipe.set('foo', 'bar').sadd('faz', 'baz').incr('auto_number').execute()

* Pubsub
 * p = r.pubsub(); p.subscribe('my-first-channel', 'my-second-channel', ...); p.get_message()


All properties:
 '__class__',
 '__contains__',
 '__delattr__',
 '__delitem__',
 '__dict__',
 '__dir__',
 '__doc__',
 '__eq__',
 '__format__',
 '__ge__',
 '__getattribute__',
 '__getitem__',
 '__gt__',
 '__hash__',
 '__init__',
 '__init_subclass__',
 '__le__',
 '__lt__',
 '__module__',
 '__ne__',
 '__new__',
 '__reduce__',
 '__reduce_ex__',
 '__repr__',
 '__setattr__',
 '__setitem__',
 '__sizeof__',
 '__str__',
 '__subclasshook__',
 '__weakref__',
 '_georadiusgeneric',
 '_use_lua_lock',
 '_zaggregate',
 'append',
 'bgrewriteaof',
 'bgsave',
 'bitcount',
 'bitop',
 'bitpos',
 'blpop',
 'brpop',
 'brpoplpush',
 'client_getname',
 'client_kill',
 'client_list',
 'client_setname',
 'cluster',
 'config_get',
 'config_resetstat',
 'config_rewrite',
 'config_set',
 'connection_pool',
 'dbsize',
 'debug_object',
 'decr',
 'delete',
 'dump',
 'echo',
 'eval',
 'evalsha',
 'execute_command',
 'exists',
 'expire',
 'expireat',
 'flushall',
 'flushdb',
 'from_url',
 'geoadd',
 'geodist',
 'geohash',
 'geopos',
 'georadius',
 'georadiusbymember',
 'get',
 'getbit',
 'getrange',
 'getset',
 'hdel',
 'hexists',
 'hget',
 'hgetall',
 'hincrby',
 'hincrbyfloat',
 'hkeys',
 'hlen',
 'hmget',
 'hmset',
 'hscan',
 'hscan_iter',
 'hset',
 'hsetnx',
 'hstrlen',
 'hvals',
 'incr',
 'incrby',
 'incrbyfloat',
 'info',
 'keys',
 'lastsave',
 'lindex',
 'linsert',
 'llen',
 'lock',
 'lpop',
 'lpush',
 'lpushx',
 'lrange',
 'lrem',
 'lset',
 'ltrim',
 'mget',
 'move',
 'mset',
 'msetnx',
 'object',
 'parse_response',
 'persist',
 'pexpire',
 'pexpireat',
 'pfadd',
 'pfcount',
 'pfmerge',
 'ping',
 'pipeline',
 'psetex',
 'pttl',
 'publish',
 'pubsub',
 'pubsub_channels',
 'pubsub_numpat',
 'pubsub_numsub',
 'randomkey',
 'register_script',
 'rename',
 'renamenx',
 'response_callbacks',
 'restore',
 'rpop',
 'rpoplpush',
 'rpush',
 'rpushx',
 'sadd',
 'save',
 'scan',
 'scan_iter',
 'scard',
 'script_exists',
 'script_flush',
 'script_kill',
 'script_load',
 'sdiff',
 'sdiffstore',
 'sentinel',
 'sentinel_get_master_addr_by_name',
 'sentinel_master',
 'sentinel_masters',
 'sentinel_monitor',
 'sentinel_remove',
 'sentinel_sentinels',
 'sentinel_set',
 'sentinel_slaves',
 'set',
 'set_response_callback',
 'setbit',
 'setex',
 'setnx',
 'setrange',
 'shutdown',
 'sinter',
 'sinterstore',
 'sismember',
 'slaveof',
 'slowlog_get',
 'slowlog_len',
 'slowlog_reset',
 'smembers',
 'smove',
 'sort',
 'spop',
 'srandmember',
 'srem',
 'sscan',
 'sscan_iter',
 'strlen',
 'substr',
 'sunion',
 'sunionstore',
 'time',
 'touch',
 'transaction',
 'ttl',
 'type',
 'unwatch',
 'wait',
 'watch',
 'zadd',
 'zcard',
 'zcount',
 'zincrby',
 'zinterstore',
 'zlexcount',
 'zrange',
 'zrangebylex',
 'zrangebyscore',
 'zrank',
 'zrem',
 'zremrangebylex',
 'zremrangebyrank',
 'zremrangebyscore',
 'zrevrange',
 'zrevrangebylex',
 'zrevrangebyscore',
 'zrevrank',
 'zscan',
 'zscan_iter',
 'zscore',
 'zunionstore']
'''




def run_tests(deps_provider):
    '''
    '''
    import doctest, sys
    import seneca.smart_contract_tester as scft
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
