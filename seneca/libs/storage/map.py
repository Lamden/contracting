from seneca.engine.interpret.utils import ItemNotFoundException
from seneca.libs.storage.datatype import DataType, POINTER_KEY
from seneca.libs.storage.registry import Registry


class Map(DataType):

    def __getitem__(self, k):
        pointer = self.driver.hget(self.key, POINTER_KEY)
        if pointer:
            res = self.driver.hget(pointer.decode(), k)
        else:
            res = self.driver.hget(self.key, k)
        if not res:
            raise ItemNotFoundException('Cannot find {} in {}'.format(k, self.__repr__))
        return self.decode(res)

    def __setitem__(self, k, v):
        return self.driver.hset(self.key, k, self.encode(v))


Registry.register_class('Map', Map)
