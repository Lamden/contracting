from seneca.engine.interpret.parser import Parser
from decimal import Decimal
from seneca.libs.storage.registry import Registry
import ujson as json

DELIMITER = ':'
POINTER = '&'
SORTED_TYPE = '~'
TYPE_SEPARATOR = '@'
NUMBER_TYPES = (int, float)
APPROVED_TYPES = (Decimal, str, bool, bytes)
RESOURCE_KEY = '__resources__'
PROPERTY_KEY = '__properties__'
INDEX_SEPARATOR = '.'


class Encoder(object):

    default_value = None

    def encode(self, value, key=None, final_dump=True):
        if issubclass(type(value), DataType):
            original_key = repr(value)
            key_parts = original_key.split(DELIMITER)
            parent_key = DELIMITER.join(key_parts[:2])
            new_key = DELIMITER.join([parent_key, self.resource, key])
            if self.driver.exists(original_key) and final_dump:
                if value.__class__.__name__ == 'Table':
                    new_value = '{}{}'.format(POINTER, original_key)
                    self.driver.hset(self.key, key, new_value)
                else:
                    self.driver.rename(original_key, new_key)
                return
            else:
                return '{}{}'.format(POINTER, new_key)
        elif type(value) in (tuple, list):
            value = [self.encode(v, key=key, final_dump=False) for v in value]
            value = json.dumps(value)
        elif final_dump:
            value = json.dumps(value)
        return value

    def decode(self, value, resource=None):
        if not value:
            if resource:
                cls = self.__class__
                return cls(resource, cls.default_value, placeholder=True)
            return self.default_value
        value = value.decode()
        if value[0] == POINTER:
            data_type_name, _, key = value[1:].split(DELIMITER, 2)
            key_parts = key.split(INDEX_SEPARATOR)
            data_type = Registry.get_data_type(data_type_name)
            data_type_obj = data_type(key_parts[0], placeholder=True)
        else:
            data_type_obj = json.loads(value)
            if type(data_type_obj) in NUMBER_TYPES:
                data_type_obj = Decimal(data_type_obj)
        return data_type_obj


class DataTypeProperties:
    @property
    def driver(self):
        return Parser.executor.driver

    @property
    def rt(self):
        return Parser.parser_scope['rt']

    @property
    def key(self):
        return DELIMITER.join([self.__class__.__name__, self.rt['contract'], self.resource])

    @property
    def top_level_key(self):
        parts = repr(self).split(DELIMITER)
        return DELIMITER.join(parts[:2] + [parts[-1]])


class DataType(Encoder, DataTypeProperties):

    def __new__(cls, *args, **kwargs):
        if kwargs.get('default_value') is not None and not kwargs.get('placeholder'):
            ValueType = Registry.get_value_type(type(kwargs['default_value']).__name__)
            class_name = ValueType.__name__.capitalize() + cls.__name__
            new_class = type(class_name, (cls, ValueType), {})
            Registry.register_class(class_name, new_class)
            return cls.__new__(new_class)

        Registry.register_class(cls.__name__, cls)
        return super().__new__(cls)

    def __init__(self, resource, default_value=None, placeholder=False, *args, **kwargs):
        self.resource = resource
        self.database = self.driver
        if default_value is not None:
            self.default_value = default_value

        if not placeholder:
            property_hash = '{}{}{}'.format(self.rt['contract'], INDEX_SEPARATOR, PROPERTY_KEY)
            if not Parser.parser_scope.get('resources', {}).get(self.rt['contract'], {}).get(resource):
                assert not self.driver.hexists(property_hash, resource), 'A {} named "{}" has already been created'.format(self.__class__.__name__, resource)
                self.driver.hset(property_hash, resource, self.__class__.__name__)

    def __repr__(self):
        return self.key

    # def __getitem__(self, k):
    #     pointer = self.driver.hget(self.key, POINTER_KEY)
    #     if pointer:
    #         res = self.driver.hget(pointer.decode(), k)
    #     else:
    #         res = self.driver.hget(self.key, k)
    #     if not res:
    #         key = self.key.split(DELIMITER, 2)[-1]
    #         default_obj = self.__class__(key, default_value=self.default_value, placeholder=True)
    #         return default_obj
    #     if res[0] == POINTER_KEY:
    #         res = self.driver.hget(res.decode(), k)
    #     return self.decode(res)
    #
    # def __setitem__(self, k, v):
    #     self.driver.hset(self.key, k, self.encode(v))

    def __getitem__(self, key):
        resource = '{}{}{}'.format(self.key.split(DELIMITER, 2)[-1], DELIMITER, key)
        return self.decode(super().__getitem__(key), resource=resource)

    def __setitem__(self, key, value):
        value = self.encode(value, key=key)
        if value:
            super().__setitem__(key, value)

