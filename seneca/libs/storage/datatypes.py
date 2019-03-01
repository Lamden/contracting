from seneca.libs.storage.resource import Resource
from seneca.libs.storage.table import Table
from seneca.libs.storage.datatype import DataType
from walrus.containers import Hash as WHash, Set as WSet, List as WList, ZSet as WZSet, BitField as WBitField
from walrus.containers import BloomFilter as WBloomFilter, Array as WArray, HyperLogLog as WHyperLogLog
from walrus.containers import chainable_method


class Hash(DataType, WHash):

    default_value = {}

    @chainable_method
    def update(self, kwargs):
        super().update(**{k: self.encode(v) for k, v in kwargs.items()})


class Set(DataType, WSet):
    pass


class List(DataType, WList):
    pass


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
