from seneca.engine.interpret.parser import Parser
from decimal import Decimal
from seneca.libs.storage.registry import Registry

DELIMITER = ':'
POINTER = '*'
SORTED_TYPE = '~'
TYPE_SEPARATOR = '@'
NUMBER_TYPES = (int, float)
APPROVED_TYPES = (Decimal, str, bool, bytes)
RESOURCE_KEY = '__resources__'
PROPERTY_KEY = '__properties__'


class DataType(object):
    def __init__(self, resource, *args, **kwargs):
        self.resource = resource

    @property
    def driver(self):
        return Parser.executor.driver

    @property
    def rt(self):
        return Parser.parser_scope['rt']

    @property
    def key(self):
        return repr(self)

    @property
    def top_level_key(self):
        parts = repr(self).split(DELIMITER)
        return DELIMITER.join(parts[:2] + [parts[-1]])

    def __repr__(self):
        return DELIMITER.join([self.__class__.__name__, self.rt['contract'], self.resource])

    def encode(self, value):
        if issubclass(type(value), DataType):
            value = '{}{}'.format(POINTER, value)
        else:
            value = '{}{}{}'.format(value, TYPE_SEPARATOR, type(value).__name__)
        return value

    def decode(self, value):
        value = value.decode()
        if value[0] == POINTER:
            data_type_name, resource, key = value[1:].split(DELIMITER)
            data_type = Registry.get_data_type(data_type_name)
            data_type_obj = data_type(DELIMITER.join([self.resource, key]))
        else:
            value, value_type = value.rsplit(TYPE_SEPARATOR, 1)
            data_type = Registry.get_value_type(value_type)
            data_type_obj = data_type(value)
        return data_type_obj


