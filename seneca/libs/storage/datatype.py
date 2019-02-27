from seneca.engine.interpret.parser import Parser
from decimal import Decimal
from seneca.libs.storage.registry import Registry
import ujson as json

DELIMITER = ':'
POINTER = '*'
SORTED_TYPE = '~'
TYPE_SEPARATOR = '@'
NUMBER_TYPES = (int, float)
APPROVED_TYPES = (Decimal, str, bool, bytes)
RESOURCE_KEY = '__resources__'
PROPERTY_KEY = '__properties__'
INDEX_SEPARATOR = '.'


class Encoder(object):

    default_value = None

    def encode(self, value):
        if issubclass(type(value), DataType):
            value = '{}{}'.format(POINTER, value)
        else:
            value = json.dumps(value)
        return value

    def decode(self, value):
        if not value:
            return self.default_value
        value = value.decode()
        if value[0] == POINTER:
            data_type_name, resource, key = value[1:].split(DELIMITER)
            data_type = Registry.get_data_type(data_type_name)
            data_type_obj = data_type(DELIMITER.join([self.resource, key]))
        else:
            data_type_obj = json.loads(value)
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
    def __init__(self, resource, *args, **kwargs):
        self.resource = resource

    def __repr__(self):
        return self.key


class WalrusDataType(Encoder, DataTypeProperties):

    def __init__(self, key):
        self.database = self.driver
        self.resource = key

    def __getitem__(self, item):
        return self.decode(super().__getitem__(item))

    def __setitem__(self, key, value):
        value = self.encode(value)
        super().__setitem__(key, value)
