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
from mysql_base import SQLType

from util import auto_set_fields


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
    def __init__(self, **kwargs):
        attrs = [ 'table_name',
                  'data' # list of dictionaries
        ]

    def to_sql():
        pass

    def run():
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


class CreateTable(object):
    '''
    CREATE TABLE MyGuests (
    id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    firstname VARCHAR(30) NOT NULL,
    lastname VARCHAR(30) NOT NULL,
    email VARCHAR(50),
    reg_date TIMESTAMP
    )
    '''

    @auto_set_fields
    def __init__(self, table_name, primary_key_column_def, other_column_defs):
        pass

    def to_sql(self):
        #CONSTRAINT UC_Person UNIQUE (ID,LastName)

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
