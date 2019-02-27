from seneca.libs.storage.map import Map
from seneca.libs.storage.resource import Resource
from seneca.libs.storage.table import Table
from seneca.libs.storage.datatype import WalrusDataType
from walrus.containers import Hash as WHash, Set as WSet, List as WList, ZSet as WZSet, BitField as WBitField
from walrus.containers import BloomFilter as WBloomFilter, Array as WArray, HyperLogLog as WHyperLogLog
from walrus.containers import chainable_method


class Hash(WalrusDataType, WHash):

    default_value = {}

    @chainable_method
    def update(self, kwargs):
        super().update(**{k: self.encode(v) for k, v in kwargs.items()})


class Set(WalrusDataType, WSet):
    pass


class List(WalrusDataType, WList):
    pass


class ZSet(WalrusDataType, WZSet):
    pass


class BitField(WalrusDataType, WBitField):
    pass


class BloomFilter(WalrusDataType, WBloomFilter):
    pass


class Array(WalrusDataType, WArray):
    pass


class HyperLogLog(WalrusDataType, WHyperLogLog):
    pass
