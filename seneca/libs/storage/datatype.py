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
POINTER_KEY = '__POINTER__'


class Encoder(object):

    default_value = None

    def encode(self, value):
        if issubclass(type(value), DataType):
            original_key = repr(value)
            parent_key = self.key.split(DELIMITER, 2)[-1]
            key_parts = original_key.split(DELIMITER, 2)
            new_key = DELIMITER.join(key_parts[:-1] + [parent_key, key_parts[-1]])
            new_key_pointer = '{}{}'.format(POINTER, new_key)
            if self.driver.exists(original_key):
                self.driver.hset(new_key, POINTER_KEY, original_key)
            value = new_key_pointer
        else:
            value = json.dumps(value)
        return value

    def decode(self, value):
        if not value:
            return self.default_value
        value = value.decode()
        if value[0] == POINTER:
            data_type_name, resource, key = value[1:].split(DELIMITER, 2)
            data_type = Registry.get_data_type(data_type_name)
            data_type_obj = data_type(key, placeholder=True)
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
    def __init__(self, resource, default_value=None, placeholder=False, *args, **kwargs):
        self.resource = resource
        if default_value is not None:
            self.default_value = default_value

        if not placeholder:
            property_hash = '{}{}{}'.format(self.rt['contract'], INDEX_SEPARATOR, PROPERTY_KEY)
            if not Parser.parser_scope.get('resources', {}).get(self.rt['contract'], {}).get(resource):
                assert not self.driver.hexists(property_hash, resource), 'A {} named "{}" has already been created'.format(self.__class__.__name__, resource)
                self.driver.hset(property_hash, resource, self.__class__.__name__)

    def __repr__(self):
        return self.key


class WalrusDataType(Encoder, DataTypeProperties):

    def __init__(self, key, default_value=None):
        self.database = self.driver
        self.resource = key
        if default_value is not None:
            self.default_value = default_value

    def __getitem__(self, item):
        return self.decode(super().__getitem__(item))

    def __setitem__(self, key, value):
        value = self.encode(value)
        super().__setitem__(key, value)
