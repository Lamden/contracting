from seneca.libs.storage.resource import Resource
from seneca.libs.storage.table import Table
from seneca.libs.storage.datatype import DataType, SubscriptType
from walrus.containers import Hash as WHash, Set as WSet, List as WList, ZSet as WZSet, BitField as WBitField
from walrus.containers import BloomFilter as WBloomFilter, Array as WArray, HyperLogLog as WHyperLogLog
from walrus.containers import chainable_method

from seneca.engine.interpret.parser import Parser


class Hash(DataType, SubscriptType, WHash):

    default_value = {}

    @chainable_method
    def update(self, kwargs):
        super().update(**{k: self.encode(v) for k, v in kwargs.items()})


class Set(DataType, WSet):
    pass


class List(DataType, WList):
    pass
    # def __getitem__(self, item):
    #     """
    #     Retrieve an item from the list by index. In addition to
    #     integer indexes, you can also pass a ``slice``.
    #     """
    #     print('get', Parser.parser_scope.get('suits'))
    #     if isinstance(item, slice):
    #         start = item.start or 0
    #         stop = item.stop
    #         if not stop:
    #             stop = -1
    #         else:
    #             stop -= 1
    #         return self.database.lrange(self.key, start, stop)
    #
    #     return self.database.lindex(self.key, item)
    #
    # def __setitem__(self, idx, value):
    #     """Set the value of the given index."""
    #     print('set', idx, value)
    #     return self.database.lset(self.key, idx, value)
    #
    # def __set__(self, instance, value):
    #     print('huh', instance)


class ZSet(DataType, WZSet):
    pass


class BitField(DataType, WBitField):
    pass


class BloomFilter(DataType, WBloomFilter):
    pass


class Array(DataType, WArray):
    pass


class HyperLogLog(DataType, WHyperLogLog):
    pass
