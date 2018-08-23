from abc import ABCMeta, abstractmethod
from seneca.engine.util import auto_set_fields

class Address(metaclass=ABCMeta):
    @auto_set_fields
    def __init__(self, key):
        pass

    def base_address(self):
        """
        Address can reference sub-items in containers e.g. fields in hashmaps.
        This method returns the container's address. For simple typles it just
        returns self.
        """
        return self

    def get_local(self, data):
        pass

    def set_local(self, data):
        pass

    def __repr__(self):
        return '<RESP ADDRESS (%s) %s>' % (self.__class__.__name__, str(self.__dict__))


class ScalarAddress(Address): pass
class RHashAddress(Address): pass

class RHashFieldAddress(Address):
    @auto_set_fields
    def __init__(self, key, field):
        pass

    def base_address(self):
        return self.key

# TODO: Implement for Lists, Sets, Sorted Sets, Bitmaps, and HyperLogLogs
