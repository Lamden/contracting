from seneca.libs.storage.datatype import DataType
from seneca.constants.config import SORTED_TYPE, TYPE_SEPARATOR, \
    PROPERTY_KEY, POINTER, INDEX_SEPARATOR
from seneca.constants.whitelists import NUMBER_TYPES, APPROVED_TYPES
from decimal import Decimal
import ujson as json


class Property(object):
    def __init__(self, value_type, required=False, default=None, indexed=False, sort=False, primary_key=False):
        self.value_type = value_type
        self.primary_key = primary_key
        self.required = primary_key or required
        self.default = default
        self.indexed = primary_key or indexed
        self.sort = sort
        self.resource = None
        self.fix_assert_attributes()
        self.column_idx = None

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
        elif issubclass(type(arg), DataType):
            arg = arg.pointer_key
        return arg


class RowData:

    def __init__(self, table, data):
        self._data = data
        self._table = table

    def __repr__(self):
        obj = {}
        for k in self._table.schema:
            obj[k] = getattr(self, k)
        return '<{}.{}> = {}'.format(self._table.key, self._table.id, json.dumps(obj, indent=4))

    def __getattr__(self, item):
        try:
            table = super().__getattribute__('_table')
            column_idx = table.schema[item].column_idx
            return self._data[column_idx]
        except:
            return