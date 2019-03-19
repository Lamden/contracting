from seneca.libs.storage.resource import Resource
from seneca.libs.storage.table import Table
from seneca.libs.storage.datatype import DataType, SubscriptType
from walrus.containers import Hash as WHash, Set as WSet, List as WList, ZSet as WZSet, BitField as WBitField
from walrus.containers import BloomFilter as WBloomFilter, Array as WArray, HyperLogLog as WHyperLogLog
from walrus.containers import chainable_method


class Hash(DataType, SubscriptType, WHash):

    base_default_value = {}

    @chainable_method
    def update(self, kwargs):
        super().update(**{k: self.encode(v) for k, v in kwargs.items()})


class Set(DataType, WSet):
    pass


class List(DataType, WList):

    def __getitem__(self, key):
        return self.decode(super().__getitem__(key))

    def __setitem__(self, key, value):
        return super().__setitem__(key, self.encode(value))

    # def append(self, value):
    #     return super().append(self.encode(value))
    #
    # def prepend(self, value):
    #     return super().prepend(self.encode(value))
    #
    # def extend(self, value):
    #     return super().extend(self.encode(value))
    #
    # def insert(self, value, *args, **kwargs):
    #     return super().insert(self.encode(value), *args, **kwargs)
    #
    # def insert_before(self, value, *args, **kwargs):
    #     return super().insert_before(self.encode(value), *args, **kwargs)
    #
    # def insert_after(self, value, *args, **kwargs):
    #     return super().insert_after(self.encode(value), *args, **kwargs)

    def popleft(self):
        return self.decode(super().popleft())

    def popright(self):
        return self.decode(super().popright())

    def pop(self, *args, **kwargs):
        return self.popright(*args, **kwargs)

    def bpopleft(self, *args, **kwargs):
        return self.decode(super().bpopleft(*args, **kwargs))

    def bpopright(self, *args, **kwargs):
        return self.decode(super().bpopright(*args, **kwargs))


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
