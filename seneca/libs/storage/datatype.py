from seneca.engine.interpreter.parser import Parser
from decimal import Decimal
from seneca.libs.storage.registry import Registry
from seneca.constants.config import *
from seneca.constants.whitelists import NUMBER_TYPES
import ujson as json


class Encoder(object):

    default_value = {}
    base_default_value = None

    def encode(self, value, key=None):
        if issubclass(type(value), DataType):
            original_key = repr(value)
            new_key = DELIMITER.join([self.key, key])
            # TODO START: remove when CR includes other commands
            # *** ORIGINAL CODE START ***
            # if self.driver.exists(original_key) and not hasattr(value, 'no_rename'):
            #     self.driver.rename(original_key, new_key)
            #     return
            # elif hasattr(value, 'no_rename'):
            #     return '{}{}{}{}'.format(POINTER, original_key, INDEX_SEPARATOR, value.id)
            # else:
            #     return '{}{}'.format(POINTER, new_key)
            # *** ORIGINAL CODE END ***
            try:
                if not hasattr(value, 'no_rename'):
                    self.driver.rename(original_key, new_key)
                    return
            except:
                pass
            if hasattr(value, 'no_rename'):
                return '{}{}{}{}'.format(POINTER, original_key, INDEX_SEPARATOR, value.id)
            else:
                return '{}{}'.format(POINTER, new_key)
            # TODO END: remove when CR includes other commands

        else:
            value = json.dumps(value)
        return value

    def decode(self, value, resource=None):
        if not value:
            if resource:
                cls = self.__class__
                obj = cls(resource, cls.default_value.get(self.contract_name), placeholder=True)
                obj.contract_name = self.contract_name
                return obj
            return self.default_value.get(self.contract_name, self.base_default_value)
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
    def database(self):
        return Parser.executor.driver

    @property
    def rt(self):
        return Parser.parser_scope['rt']

    @property
    def callstack(self):
        return Parser.parser_scope.get('callstack', [])

    @property
    def key(self):
        if len(self.callstack) == 0 or self.resource.split(DELIMITER)[0] in Parser.parser_scope.get('imports', {}):
            contract_name = self.contract_name
        else:
            contract_name = self.callstack[-1][0]
        return DELIMITER.join([self.__class__.__name__, contract_name, self.resource])

    @property
    def top_level_key(self):
        parts = repr(self).split(DELIMITER)
        return DELIMITER.join(parts[:2] + [parts[-1]])


class DataType(Encoder, DataTypeProperties):

    def __new__(cls, *args, **kwargs):
        if kwargs.get('default_value') is not None and not kwargs.get('placeholder'):
            resource_name = args[0]
            ValueType = Registry.get_value_type(type(kwargs['default_value']).__name__)
            if ValueType in NUMBER_TYPES:
                ValueType = Decimal
            class_name = ValueType.__name__.capitalize() + cls.__name__
            new_class = type(class_name, (cls, ValueType), {})
            Registry.register_class(class_name, new_class)
            contract_name = Parser.parser_scope['rt']['contract']
            Parser.parser_scope['resources'][contract_name][resource_name] = class_name
            return cls.__new__(new_class)

        Registry.register_class(cls.__name__, cls)
        return super().__new__(cls)

    def __init__(self, resource, default_value=None, placeholder=False, *args, **kwargs):
        self.resource = resource
        self.contract_name = self.rt['contract']
        self.data = None
        self.access_mode = READ_WRITE_MODE
        if default_value is not None:
            self.default_value[self.contract_name] = default_value

        if not placeholder:
            if not Parser.parser_scope.get('resources', {}).get(self.rt['contract'], {}).get(resource):
                assert not self.driver.hexists(self.properties_hash, RESOURCE_KEY), 'A {} named "{}" has already been created'.format(self.__class__.__name__, resource)
                self.driver.hset(self.properties_hash, RESOURCE_KEY, resource)

    def __repr__(self):
        return self.key

    def set_data(self, data):
        self.data = data

    @property
    def pointer_key(self):
        return '{}{}'.format(POINTER, self.key)

    @property
    def properties_hash(self):
        return '{}{}{}'.format(self.key, TYPE_SEPARATOR, PROPERTY_KEY)


class SubscriptType:

    def __getitem__(self, key):
        resource = '{}{}{}'.format(self.key.split(DELIMITER, 2)[-1], DELIMITER, key)
        return self.decode(super().__getitem__(key), resource=resource)

    def __setitem__(self, key, value):
        if not Parser.parser_scope.get('__safe_execution__'):
            assert self.access_mode == READ_WRITE_MODE, 'Not allowed to write to resource "{}" in this scope'.format(self.key)
        value = self.encode(value, key=key)
        if value:
            super().__setitem__(key, value)
