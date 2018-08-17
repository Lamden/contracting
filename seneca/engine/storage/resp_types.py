from seneca.engine.util import auto_set_fields
from seneca.engine.storage import resp_commands as coms

class RType(): pass
class RScalar(ContainerType): pass
class ScalarRaw(RScalar): pass
class ScalarString(RScalar): pass
class ScalarInt(RScalar): pass
class ScalarFloat(RScalar): pass

class RHash(ContainerType): pass
class RList(ContainerType): pass
class RSet(ContainerType): pass
class RSortedSet(ContainerType): pass



class AnyKey():
    def __init__(self):
        pass

    def validate_existing(self):
        return True # No constraints, always passes


class ExistingKey(AnyKey):
    @auto_set_fields
    def __init__(self, ex, key):
        pass

    def validate_existing(self):
        return self.ex(coms.Exists(self.key))


class NonExistingKey(ExistingKey):
    def validate_existing(self):
        return not super().validate_existing()


class AnyScalar(ExistingKey):
    def validate_existing(self):
        return self.ex(coms.Exists(self.key))



class AnyHashMap(ExistingKey): pass
class HashMapFieldInt(AnyHashMap): pass
class HashMapFieldFloat(AnyHashMap): pass

# class RESPList(RESPType): pass
# class RESPSet(RESPType): pass
# class RESPSortedSet(RESPType): pass
# class RESPBitmap(RESPType): pass
# class RESPHyperLogLog(RESPType): pass
