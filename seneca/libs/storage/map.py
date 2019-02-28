from seneca.engine.interpret.utils import ItemNotFoundException
from seneca.libs.storage.datatype import DataType, POINTER_KEY, DELIMITER
from seneca.libs.storage.registry import Registry


class Map(DataType):

    def __getitem__(self, k):
        pointer = self.driver.hget(self.key, POINTER_KEY)
        if pointer:
            res = self.driver.hget(pointer.decode(), k)
        else:
            res = self.driver.hget(self.key, k)
        if not res:
            key = self.key.split(DELIMITER, 2)[-1]
            default_obj = Map(key, placeholder=True)
            return default_obj
        if res[0] == POINTER_KEY:
            print(res)
            res = self.driver.hget(res.decode(), k)
        return self.decode(res)

    def __setitem__(self, k, v):
        return self.driver.hset(self.key, k, self.encode(v))


Registry.register_class('Map', Map)
