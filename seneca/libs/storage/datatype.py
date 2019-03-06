from seneca.engine.interpreter.parser import Parser
from decimal import Decimal
from seneca.libs.storage.registry import Registry
from seneca.constants.config import *
from seneca.constants.whitelists import NUMBER_TYPES
import ujson as json


class Encoder(object):

    default_value = None

    def encode(self, value, key=None):
        if issubclass(type(value), DataType):
            original_key = repr(value)
            new_key = DELIMITER.join([self.key, key])
            if self.driver.exists(original_key) and not hasattr(value, 'no_rename'):
                self.driver.rename(original_key, new_key)
                return
            elif hasattr(value, 'no_rename'):
                return '{}{}{}{}'.format(POINTER, original_key, INDEX_SEPARATOR, value.id)
            else:
                return '{}{}'.format(POINTER, new_key)
        else:
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
            if len(key_parts) == 2:
                data_type_obj.set_data(data_type_obj.decode(self.driver.hget(data_type_obj.key, key_parts[1])))
        else:
            try: data_type_obj = json.loads(value)
            except: data_type_obj = value
            if type(data_type_obj) in NUMBER_TYPES:
                data_type_obj = Decimal(value)
        return data_type_obj


class DataTypeProperties:
    @property
    def driver(self):
        return Parser.executor.driver

    @property
    def rt(self):
        return Parser.parser_scope['rt']

    @property
    def callstack(self):
        return Parser.parser_scope.get('callstack', [])

    @property
    def key(self):
        if self.resource in Parser.parser_scope.get('imports', {}):
            contract_name = self.contract_name
        elif len(self.callstack) == 0:
            contract_name = '__main__'
        else:
            contract_name = self.callstack[-1][0]
        # contract_name = self.contract_name if self.resource in Parser.parser_scope.get('imports', {}) else self.rt['contract']
        return DELIMITER.join([self.__class__.__name__, contract_name, self.resource])

    @property
    def top_level_key(self):
        parts = repr(self).split(DELIMITER)
        return DELIMITER.join(parts[:2] + [parts[-1]])


class DataType(Encoder, DataTypeProperties):

    def __new__(cls, *args, **kwargs):
        if kwargs.get('default_value') is not None and not kwargs.get('placeholder'):
            ValueType = Registry.get_value_type(type(kwargs['default_value']).__name__)
            if ValueType in NUMBER_TYPES:
                ValueType = Decimal
            class_name = ValueType.__name__.capitalize() + cls.__name__
            new_class = type(class_name, (cls, ValueType), {})
            Registry.register_class(class_name, new_class)

            return cls.__new__(new_class)

        Registry.register_class(cls.__name__, cls)
        return super().__new__(cls)

    def __init__(self, resource, default_value=None, placeholder=False, *args, **kwargs):
        self.resource = resource
        self.database = self.driver
        self.contract_name = self.rt['contract']
        self.data = None
        if default_value is not None:
            self.default_value = default_value

        if not placeholder:
            property_hash = '{}{}{}'.format(self.rt['contract'], INDEX_SEPARATOR, PROPERTY_KEY)
            if not Parser.parser_scope.get('resources', {}).get(self.rt['contract'], {}).get(resource):
                assert not self.driver.hexists(property_hash, resource), 'A {} named "{}" has already been created'.format(self.__class__.__name__, resource)
                self.driver.hset(property_hash, resource, self.__class__.__name__)

    def __repr__(self):
        return self.key

    def set_data(self, data):
        self.data = data

    @property
    def pointer_key(self):
        return '{}{}'.format(POINTER, self.key)


class SubscriptType:

    def __getitem__(self, key):
        resource = '{}{}{}'.format(self.key.split(DELIMITER, 2)[-1], DELIMITER, key)
        return self.decode(super().__getitem__(key), resource=resource)

    def __setitem__(self, key, value):
        value = self.encode(value, key=key)
        if value:
            super().__setitem__(key, value)