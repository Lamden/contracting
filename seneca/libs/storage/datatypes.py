from seneca.engine.interpret.parser import Parser
from seneca.engine.interpret.executor import Executor
from seneca.engine.interpret.utils import NotImplementedException, ItemNotFoundException
from redis.connection import Encoder
from decimal import Decimal
import ujson as json

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
        return Parser.executor.r

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


class ResourceObj:

    instance = None

    def __set__(self, instance, value):
        ResourceObj.instance = instance
        k, v = instance.resource, value
        instance.driver.hset(instance.rt['contract'], k, instance.encode(v))
        self.instance = instance

    def __get__(self, instance, parent):
        res = instance.driver.hget(instance.rt['contract'], instance.resource)
        if not res:
            raise ItemNotFoundException('Cannot find {} in {}'.format(instance.resource, instance.__repr__))
        return instance.decode(res)


class Resource(DataType):
    resource_obj = ResourceObj()


class Map(DataType):

    def __getitem__(self, k):
        res = self.driver.hget(self.rt['contract'], k)
        if not res:
            raise ItemNotFoundException('Cannot find {} in {}'.format(k, self.__repr__))
        return self.decode(res)

    def __setitem__(self, k, v):
        return self.driver.hset(self.rt['contract'], k, self.encode(v))


class Table(DataType):

    schemas = {}

    def __init__(self, resource, schema=None, data=None):
        super().__init__(resource)
        self.schema = schema
        self.data = data
        self.register_schema()

    def register_schema(self):
        resource_name = self.top_level_key
        if Table.schemas.get(resource_name):
            self.schema = Table.schemas[resource_name]
        elif self.schema:
            for k, v in self.schema.items():
                if type(v) != SchemaArgs:
                    self.schema[k] = SchemaArgs(v)
            Table.schemas[resource_name] = self.schema
        else:
            raise AssertionError('Schema for {} is not found'.format(self.key))

    @property
    def row_id(self):
        return self.driver.hget(self.table_properties_hash, 'ROW_ID')

    @property
    def count(self):
        return self.driver.hlen(self.key)

    @property
    def index_hash(self):
        return '{}{}{}'.format(self.key, TYPE_SEPARATOR, POINTER)

    @property
    def sort_hash(self):
        return '{}{}{}'.format(self.key, TYPE_SEPARATOR, SORTED_TYPE)

    @property
    def table_properties_hash(self):
        return '{}{}{}'.format(self.key, TYPE_SEPARATOR, PROPERTY_KEY)

    def create_row(self, *args, **kwargs):
        keys = list(self.schema.keys())
        args_tuple = tuple()
        kwargs_tuple = tuple()
        for idx, arg in enumerate(args):
            k = keys[idx]
            assert not kwargs.get(k), '{} already specified in named arguments'.format(k)
            schema_arg = self.schema[k]
            arg = schema_arg.get_asserted_arg(arg)
            self.add_to_index(k, schema_arg, arg)
            self.add_to_sort(k, schema_arg, arg)
            args_tuple += (arg,)
        for k in keys[len(args):]:
            schema_arg = self.schema[k]
            kwarg = kwargs.get(k)
            kwarg = schema_arg.get_asserted_arg(kwarg)
            self.add_to_index(k, schema_arg, kwarg)
            self.add_to_sort(k, schema_arg, kwarg)
            kwargs_tuple += (kwarg,)
        data = args + kwargs_tuple
        return Table(self.resource, self.schema, data)

    def add_to_index(self, field, schema_arg, arg):
        # Populate index
        if schema_arg.indexed:
            index_hash = self.index_hash + field
            self.driver.hset(index_hash, arg, self.row_id)

    def add_to_sort(self, field, schema_arg, arg):
        if schema_arg.sort:
            sort_hash = self.sort_hash + field
            print(sort_hash, field, arg)
            # self.driver.zadd(sort_hash, arg, field)

    def add_row(self, *args, **kwargs):
        self.driver.hincrby(self.table_properties_hash, 'ROW_ID', 1)
        row = self.create_row(*args, **kwargs)
        self.driver.hset(self.key, self.row_id, self.encode(row.data))
        return row

    def delete_rows(self, idx=None):
        return self.driver.hdel(self.key, idx)

    def delete_table(self):
        # Delete indexes and sort
        for field, arg in self.schema.items():
            if arg.indexed:
                index_hash = self.index_hash + field
                self.driver.delete(index_hash)
            if arg.sort:
                sort_hash = self.sort_hash + field
                self.driver.delete(sort_hash)

        # Delete table list
        self.driver.delete(self.resource)
        self.driver.delete(self.table_properties_hash)
        self.driver.delete(self.key)

        # De-register schema
        resource_name = self.top_level_key
        if Table.schemas.get(resource_name):
            del Table.schemas[resource_name]

    def find(self, field=None, matches=None, exactly=None, limit=100):
        if field:
            if not self.schema.get(field):
                raise AssertionError('No field named "{}"'.format(field))
            if not self.schema[field].indexed:
                raise AssertionError('Field "{}" is not indexed and hence not queryable'.format(field))
            index_hash = self.index_hash + field
            if exactly:
                idx = self.driver.hget(index_hash, exactly)
                res = [self.driver.hget(self.key, idx)]
            elif matches:
                _, idxs = self.driver.hscan(index_hash, match=matches, count=limit)
                res = self.driver.hmget(self.key, idxs.values())
        else:
            res = self.driver.hgetall(self.key)
            return [self.decode(r) for k, r in res.items()]
        return [self.decode(r) for r in res]


class SchemaArgs(object):
    def __init__(self, value_type, required=False, default=None, indexed=False, sort=False, primary_key=False):
        self.value_type = value_type
        self.required = primary_key or required
        self.default = default
        self.indexed = primary_key or indexed
        self.sort = sort
        self.resource = None
        self.fix_assert_attributes()

    def fix_assert_attributes(self):

        # Snap value type to Decimal
        if self.value_type in NUMBER_TYPES:
            self.value_type = Decimal

        # Disapproves types outside of whitelist
        if self.value_type not in APPROVED_TYPES and not issubclass(type(self.value_type), DataType):
            raise AssertionError('Type {} is not allowed in schemas'.format(type(self.value_type)))

        # Set the correct value_type type for DataTypes in the schema
        if issubclass(type(self.value_type), DataType):
            self.resource = self.value_type.resource
            self.value_type = type(self.value_type)

        # Set default values
        if self.default is None:
            if self.value_type == str:
                self.default = ''
            elif issubclass(self.value_type, Decimal):
                self.default = Decimal(0)
            elif self.value_type == bool:
                self.default = bool
            elif self.value_type == bytes:
                self.default = b''

    def get_asserted_arg(self, arg):

        # Interpret value as Decimal
        if type(arg) in NUMBER_TYPES:
            arg = Decimal(arg)

        # Make assertions on args or set it to its default value
        if arg is None:
            if self.required:
                raise AssertionError('Field of type {} is required'.format(self.value_type))
            else:
                arg = self.default
        elif issubclass(type(arg), DataType) and arg.resource != self.resource:
            raise AssertionError('DataType {} must have the resource "{}"'.format(type(arg), self.resource))
        elif type(arg) != self.value_type:
            raise AssertionError('Arg {} must be of type {}'.format(arg, self.value_type))

        return arg


class Registry:
    @classmethod
    def get_data_type(cls, class_name):
        data_type_class = {
            'Map': Map,
            'Table': Table
        }.get(class_name)
        assert data_type_class, 'DataType "{}" not found!'.format(class_name)
        return data_type_class

    @classmethod
    def get_value_type(cls, value_type_name):
        value_type = {
            'int': Decimal,
            'float': Decimal,
            'Decimal': Decimal,
            'str': str,
            'bool': bool,
            'bytes': bytes,
            'tuple': eval
        }.get(value_type_name)
        assert value_type, 'DataType "{}" not found!'.format(value_type_name)
        return value_type