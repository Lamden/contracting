'''
* mysql-base lib
  * Defines serializable query class
  * Functions for stuff like sanitizing data
  * Actually runs queries from query object

classes
read_query
write_row_query
insert_row
edit_table

* TODO: consider using an abstract base class.
'''

from typing import Type, Dict, Tuple, List
#cls: Type[A]

import mysql_query_fragments as frag
from mysql_base import SQLType, get_py_to_sql_cast_func
from util import *


class ColumnDefinition(object):
    '''Describes a column name, type, and unique constraint'''

    @auto_set_fields
    def __init__(self, name, sql_type, is_unique=False):
        pass

    def to_sql(self):
        return '%s %s' % (self.name, self.sql_type)


class AutoIncrementColumn(ColumnDefinition):
    '''A specific column definition for auto increment columns.'''

    @auto_set_fields
    def __init__(self, name: str):
        self.sql_type = 'BIGINT'# TODO: figure out if this should be INT or BIGINT
        self.is_unique = False

    def to_sql(self):
        return '%s %s unsigned NOT NULL AUTO_INCREMENT' % (self.name, self.sql_type)


class UpdateRows(object):

    @auto_set_fields
    def __init__(self, table_name, constraints, data):
        pass

    def to_sql():
        pass

    def run():
        pass


class InsertRows(object):
    '''
    INSERT INTO table_name
    (column1, column2, column3, ...)
    VALUES
    (value1, value2, value3, ...)
    ;
    '''
    @auto_set_fields
    def __init__(self, table_name, column_names, list_of_values_lists):
        pass

    def to_sql(self):
        correct_len = len(self.column_names)

        for value_list in self.list_of_values_lists:
            assert len(value_list) == correct_len

        casting_funcs = [get_py_to_sql_cast_func(x) for x in self.list_of_values_lists[0]]

        def apply_funcs(xs):
            ''' Apply list of functions over a list of values '''
            return [ f(x) for (f, x) in zip(casting_funcs, xs)]

        def format_values(xs):
            return '(%s)' % ', '.join(xs)

        convert_data_list_to_string = compose(format_values, apply_funcs)
        
        formatted_values_lists = [convert_data_list_to_string(x) for x in self.list_of_values_lists]

        return '\n'.join([
          'INSERT INTO %s' % self.table_name,
          '(%s)' % ', '.join(self.column_names),
          'VALUES',
          ', '.join(formatted_values_lists),
          ';'
        ])

    def run(self):
        pass


class DescribeTable(object):
    '''

    '''
    pass


class SelectRows(object):
    def __init__(self, **kwargs):
        attrs = [ 'table_name',
                  'fields',
                  'constraints',
        ]

    def to_sql():
        pass

    def run():
        pass


class AddTableColumn(object):
    '''
    ALTER TABLE table_name;
    ALTER COLUMN column_name datatype;
    '''
    def __init__(self, **kwargs):
        attrs = [ 'table_name',
                      'column_name',
                      'column_type',
                      'column_is_unique',
        ]

    def to_sql():
        pass

    def run():
        pass


class DropTableColumn(object):
        @auto_set_fields
        def __init__(self, table_name, column_name):
            pass

        def to_sql():
            pass

        def run():
            pass


class DropTable(object):
    '''
    DROP TABLE table_name;
    '''
    @auto_set_fields
    def __init__(self, table_name):
        pass

    def to_sql(self):
        return 'DROP TABLE %s;' % self.table_name

    def run(self):
        pass


class CreateTable(object):
    ''' Example:
    CREATE TABLE test_users (
    id BIGINT unsigned NOT NULL AUTO_INCREMENT PRIMARY_KEY,
    username VARCHAR(30),
    first_name VARCHAR(30),
    balance BIGINT,
    CONSTRAINT UC_test_users UNIQUE (id,username)
    );
    '''
    @auto_set_fields
    def __init__(self, table_name, primary_key_column_def, other_column_defs):
        pass

    def to_sql(self):
        column_def_strs = (
          [self.primary_key_column_def.to_sql() + ' PRIMARY_KEY'] +
          list(map(lambda x: x.to_sql(), self.other_column_defs))
        )

        unique_column_names = [self.primary_key_column_def.name] + \
          [x.name for x in self.other_column_defs if x.is_unique]

        constraint_sql = 'CONSTRAINT UC_%s UNIQUE (%s)' % \
          (self.table_name, ','.join(unique_column_names))

        table_spec = ',\n'.join(column_def_strs + [constraint_sql])

        return '\n'.join([
          'CREATE TABLE %s (' % self.table_name,
          table_spec,
          ');'
        ])

    def run(self):
        pass


if __name__ == '__main__':
    print(CreateTable(
      'test_users',
      AutoIncrementColumn('id'),
      [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
        ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
        ColumnDefinition('balance', SQLType('BIGINT'), False),
      ]
    ).to_sql())

    print(InsertRows('test_users', ['username', 'first_name', 'balance'],
        [['tester', 'test', 500],
         ['tester2', 'two', 200],
        ]).to_sql())
