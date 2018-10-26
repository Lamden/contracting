import redis

# TODO -- clean this file up

READ_METHODS = {'get', 'zscore', 'zrevrangebyscore', 'zrangebyscore'}
WRITE_METHODS = {'set', 'hmset', 'zadd', 'zrem', 'zincrby'}

class RedisProxy:

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, contract_idx: int):
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

    def __getattr__(self, item):
        pass


class RObjectMeta(type):
    all_reads = set()
    all_writes = set()

    def __new__(cls, clsname, bases, clsdict):
        clsobj = super().__new__(cls, clsname, bases, clsdict)
        # print("[MetaClass] creating new class named {}, which has reads: {}".format(clsname, clsobj._READ_METHODS))
        cls._combine_sets_if_exists(clsobj, '_READ_METHODS', 'all_reads')
        cls._combine_sets_if_exists(clsobj, '_WRITE_METHODS', 'all_writes')
        return clsobj

    @classmethod
    def _combine_sets_if_exists(cls, clsobj, set_to_add: str, set_to_add_to: str):
        """
        Adds all of the elements in set_to_add to set_to_add_to.
        """
        if hasattr(clsobj, set_to_add):
            assert hasattr(clsobj, set_to_add_to), "Class {} has no attribute {}".format(clsobj, set_to_add_to)
            set_to_add_to = getattr(clsobj, set_to_add_to)

            for element in getattr(clsobj, set_to_add):
                set_to_add_to.add(element)



class Base(metaclass=RObjectMeta):
    _READ_METHODS = set()
    _WRITE_METHODS = set()


class Test1(Base):
    _READ_METHODS = {'test1_read'}

class Test2(Base):
    _READ_METHODS = {'test2_read'}


print("ALL_READS: {}".format(Base.all_reads))
# class MessageBaseMeta(type):
#     def __new__(cls, clsname, bases, clsdict):
#         clsobj = super().__new__(cls, clsname, bases, clsdict)
#         if not hasattr(clsobj, 'registry'):
#             clsobj.registry = {}
#
#         # Define an "undirected" mapping between classes and their enum vals
#         m = hashlib.md5()
#         m.update(clsobj.__name__.encode())
#         l = int(m.digest().hex(), 16) % pow(2, 16)
#         assert clsobj.registry.get(l) is None, 'Registry enum collision of message class {}! Collided with {}'.format(
#             clsobj.__name__, clsobj.registry.get(l))
#
#         clsobj.registry[clsobj] = l
#         clsobj.registry[l] = clsobj
#
#         return clsobj