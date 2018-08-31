import sys
import imp
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)


class RedisImportFinder:

    def find_module(self, fullname, path=None):
        print('looking for {!r} with path {!r}'.format(fullname, path))

        if fullname[0:2] == 'c_':
            return RedisImportLoader()
        return None


class RedisImportLoader:

    def get_code(self, fullname):
        return r.get(fullname)

    def load_module(self, fullname):
        print(fullname)
        code = self.get_code(fullname)
        if code is None:
            return None
        ispkg = False  # self.is_package(fullname)
        mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
        mod.__file__ = "<%s>" % self.__class__.__name__
        mod.__loader__ = self
        if ispkg:
            mod.__path__ = []
            mod.__package__ = fullname
        else:
            mod.__package__ = fullname.rpartition('.')[0]
        exec(code, mod.__dict__)
        return mod


def initialize_redis_loader():
    sys.meta_path.append(RedisImportFinder())
