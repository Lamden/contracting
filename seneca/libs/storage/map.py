from seneca.engine.interpret.utils import ItemNotFoundException
from seneca.libs.storage.datatype import DataType
from seneca.libs.storage.registry import Registry


class Map(DataType):

    def __getitem__(self, k):
        res = self.driver.hget(self.rt['contract'], k)
        if not res:
            raise ItemNotFoundException('Cannot find {} in {}'.format(k, self.__repr__))
        return self.decode(res)

    def __setitem__(self, k, v):
        return self.driver.hset(self.rt['contract'], k, self.encode(v))


Registry.register_class('Map', Map)
