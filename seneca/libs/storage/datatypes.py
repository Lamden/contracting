from seneca.libs.storage.map import Map
from seneca.libs.storage.resource import Resource
from seneca.libs.storage.table import Table
from seneca.libs.storage.datatype import WalrusDataType
from walrus.containers import *


class WHash(WalrusDataType, Hash):

    default_value = {}

    @chainable_method
    def update(self, kwargs):
        super().update(**{k: self.encode(v) for k, v in kwargs.items()})


class WSet(WalrusDataType, Set):
    pass


class WList(WalrusDataType, List):
    pass


class WZSet(WalrusDataType, ZSet):
    pass


class WBitField(WalrusDataType, BitField):
    pass


class WBloomFilter(WalrusDataType, BloomFilter):
    pass


class WArray(WalrusDataType, Array):
    pass


class WHyperLogLog(WalrusDataType, HyperLogLog):
    pass
