from seneca.libs.storage.datatype import DataType, NUMBER_TYPES, APPROVED_TYPES, SORTED_TYPE, TYPE_SEPARATOR, \
    PROPERTY_KEY, POINTER, INDEX_SEPARATOR
from seneca.libs.storage.registry import Registry
from decimal import Decimal


class Property(object):
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


class Table(DataType):

    schemas = {}

    def __init__(self, resource, schema=None, data=None, *args, **kwargs):
        super().__init__(resource, *args, **kwargs)
        self.schema = schema
        self.data = data
        self.register_schema()

    def register_schema(self):
        resource_name = self.top_level_key
        if Table.schemas.get(resource_name):
            self.schema = Table.schemas[resource_name]
        elif self.schema:
            column_idx = 0
            for k, v in self.schema.items():
                if type(v) != Property:
                    self.schema[k] = Property(v)
                self.driver.hset(self.properties_hash, k, column_idx)
                column_idx += 1
            Table.schemas[resource_name] = self.schema
        else:
            raise AssertionError('Schema for {} is not found'.format(self.key))

    @property
    def row_id(self):
        return self.driver.hget(self.properties_hash, '__ROW_ID__')

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
    def properties_hash(self):
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
            args_tuple += (arg,)
        for k in keys[len(args):]:
            schema_arg = self.schema[k]
            kwarg = kwargs.get(k)
            kwarg = schema_arg.get_asserted_arg(kwarg)
            self.add_to_index(k, schema_arg, kwarg)
            kwargs_tuple += (kwarg,)
        data = args + kwargs_tuple
        return Table(self.resource, self.schema, data, placeholder=True)

    def add_to_index(self, field, schema_arg, arg):
        # Populate index
        if schema_arg.sort:
            index_hash = self.index_hash + field + INDEX_SEPARATOR + arg
            self.driver.hset(index_hash, self.row_id, arg)
        elif schema_arg.indexed:
            index_hash = self.index_hash + field + INDEX_SEPARATOR + arg
            self.driver.hset(index_hash, self.row_id, 1)

    def remove_from_index(self):
        pass

    def add_row(self, *args, **kwargs):
        self.driver.hincrby(self.properties_hash, '__ROW_ID__', 1)
        row = self.create_row(*args, **kwargs)
        self.driver.hset(self.key, self.row_id, self.encode(row.data))
        return row

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
        keys = self.driver.keys(self.key+'*')
        self.driver.delete(*keys)

        # De-register schema
        resource_name = self.top_level_key
        if Table.schemas.get(resource_name):
            del Table.schemas[resource_name]

    def _find_items(self, property=None, matches=None, exactly=None, limit=100):
        if not self.schema.get(property):
            raise AssertionError('No property named "{}"'.format(property))
        if not self.schema[property].indexed:
            raise AssertionError('Property "{}" is not indexed and hence not queryable'.format(property))
        index_hash = self.index_hash + property
        if exactly:
            query_hash = index_hash + INDEX_SEPARATOR + exactly
            idxs = list(self.driver.hgetall(query_hash).keys())[:limit]
        elif matches:
            query = '{}{}{}'.format(index_hash, INDEX_SEPARATOR, matches)
            _, keys = self.driver.scan(match=query, count=limit)
            idxs = set()
            for k in keys:
                idxs.update(self.driver.hgetall(k))
        else:
            raise AssertionError('You specify matches or exactly for this property.')
        return idxs

    def _find_operation(self, fields):
        if set(('$and', '$or')).intersection(fields.keys()):
            all_idxs = None
        else:
            conditions = {f[1:]: val for f, val in fields.items() if f[0] == '$'}
            return self._find_items(**conditions)
        for op in fields:
            for field, condition in fields[op].items():
                condition['$property'] = field
                idxs = self._find_operation(condition)
                if not all_idxs: all_idxs = set(idxs)
                if op == '$and':
                    all_idxs = all_idxs.intersection(idxs)
                elif op == '$or':
                    all_idxs = all_idxs.union(idxs)
        return all_idxs

    def find(self, fields, columns=None, column=None):
        idxs = self._find_operation(fields)
        res = self.driver.hmget(self.key, idxs)
        if column:
            column_idx = int(self.driver.hget(self.properties_hash, column))
            objs = []
            for r in res:
                r = self.decode(r)
                objs.append(r[column_idx])
        elif columns:
            assert type(columns) == list, 'Columns must be list of properties'
            column_idxs = [int(idx) for idx in self.driver.hmget(self.properties_hash, columns)]
            objs = []
            for r in res:
                r = self.decode(r)
                objs.append([r[idx] for idx in column_idxs])
        else:
            objs = [self.decode(r) for r in res if r]
        return objs

    def find_one(self, *args, **kwargs):
        objs = self.find(*args, **kwargs)
        return objs[0]

    def delete(self, *args, **kwargs):
        res = self._find_field(*args, **kwargs)
        raise AssertionError('Not Implemented')
        # return self.driver.hdel(self.key, idx)

    def update(self, updates={}, *args, **kwargs):
        res = self._find_field(*args, **kwargs)
        raise AssertionError('Not Implemented')


Registry.register_class('Table', Table)
