from seneca.engine.interpret.utils import ItemNotFoundException
from seneca.libs.storage.datatype import DataType
from seneca.libs.storage.registry import Registry


class ResourceObj:

    instance = None

    def __set__(self, instance, value):
        k, v = instance.resource, value
        instance.driver.hset(instance.rt['contract'], k, instance.encode(v))

    def __get__(self, instance, parent):
        res = instance.driver.hget(instance.rt['contract'], instance.resource)
        if not res:
            raise ItemNotFoundException('Cannot find {} in {}'.format(instance.resource, instance.__repr__()))
        return instance.decode(res)


class Resource(DataType):
    resource_obj = ResourceObj()


Registry.register_class('Resource', Resource)
