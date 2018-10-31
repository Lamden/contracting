'''
Defines intermedite representation of mysql queries.
Representations are serializable and easy to analyze and augment.

* TODO: Type annoations
* TODO: have to be very careful with joins and '.' in fields, else people will
 potentially be able to write into other tabless
* TODO: consider using an abstract base class.
* TODO: replace asserts with raising custom exception type.
* TODO: figure out escaping/backticks
* TODO: Some basic joins?
* TODO: columnRows data type, fixed length, enter data positionally or dict, nice print
* TODO: Handle column name _count

* TODO: maybe do table exists
* TODO: order_by_desc
* TODO: get_table
* TODO: add order_by and limit to delete query

* TODO: Make API more consistent across inserts, updates, and upserts

NOTE: This module doesn't handle security, that must be done upstream.

NOTE: We don't enforce caller to have any criteria, i.e. without "WHERE" all
rows will be updated, this enforcement should be added in a higher level API to
prevent accidental updates of all records.
'''
from typing import Type, Dict, Tuple, List

#cls: Type[A]

from seneca.engine.storage.mysql_base import SQLType, get_py_to_sql_cast_func, cast_py_to_sql, escape_sql_pattern, TabularKVs, py_mysql_dict
from seneca.engine.util import *

class Query(object):
    pass


class QueryComponent(object):
    pass


### Query Parts ###
class ColumnDefinition(QueryComponent):
    '''Describes a column name, type, and unique constraint
    (Covered in other tests)
    '''
    @auto_set_fields
    def __init__(self, name, sql_type, unique=False):
        pass

    def to_sql(self):
        return intercalate(' ', [
          self.name,
          str(self.sql_type),
          'UNIQUE' if self.unique else None,
        ])


class AutoIncrementColumn(ColumnDefinition):
    '''A specific column definition for auto increment columns, intended for IDs.
    (Covered in other tests)
    '''
    @auto_set_fields
    def __init__(self, name: str):
        self.sql_type = 'BIGINT'# TODO: figure out if this should be INT or BIGINT
        self.is_unique = False

    def to_sql(self):
        return '%s %s unsigned NOT NULL AUTO_INCREMENT' % (self.name, self.sql_type)


class NonNullableBooleanColumn(ColumnDefinition):
    # Note: this is not intended for inclusion in end-user libs. Non-nullable
    # interferes with SPITS snapshotting.
    @auto_set_fields
    def __init__(self, name: str):
        self.sql_type = 'Boolean'
        self.is_unique = False

    def to_sql(self):
        return '%s %s NOT NULL DEFAULT FALSE' % (self.name, self.sql_type)


class QueryCriterion(QueryComponent):
    '''
    >>> QueryCriterion('eq', 'username', 'tester').to_sql()
    "username = 'tester'"

    >>> QueryCriterion('eq', 'username', None).to_sql()
    'username IS NULL'

    >>> QueryCriterion('ne', 'username', None).to_sql()
    'username IS NOT NULL'

    '''
    cr_types_to_strs = {
        'eq': '=',
        'ne': '!=',
        'lt': '<',
        'gt': '>',
        'le': '<=',
        'ge': '>=',
    }

    @auto_set_fields
    def __init__(self, constraint_type, field_name, comparison_value):
        assert self.constraint_type in list(self.cr_types_to_strs.keys()), "Invalid constraint type."

    def to_sql(self):
        if self.comparison_value is None:
            if self.constraint_type == 'eq':
                return "%s IS NULL" % self.field_name
            elif self.constraint_type == 'ne':
                return "%s IS NOT NULL" % self.field_name
            else:
                raise Exception("Unsupported operator with 'NONE' value only == (eq) and != (ne) are supported")
        else:
            return "%s %s %s" % (self.field_name,
                                 self.cr_types_to_strs[self.constraint_type],
                                 cast_py_to_sql(self.comparison_value),
                                )

class InvertedCriterion(QueryComponent):
    '''
    >>> InvertedCriterion(QueryCriterion('eq', 'username', 'tester')).to_sql()
    "(NOT username = 'tester')"
    '''
    @auto_set_fields
    def __init__(self, criterion):
        pass

    def to_sql(self):
        return "(NOT %s)" % self.criterion.to_sql()


class AndedCriteria(QueryComponent):
    '''
    >>> AndedCriteria(
    ...   [ QueryCriterion('eq', 'username', 'tester'),
    ...     QueryCriterion('gt', 'balance', 50)
    ... ]).to_sql()
    "(username = 'tester' AND balance > 50)"
    '''
    @auto_set_fields
    def __init__(self, criteria):
        pass

    def to_sql(self):
        return "(%s)" % ' AND '.join([x.to_sql() for x in self.criteria])


class OredCriteria(QueryComponent):
    '''
    >>> OredCriteria(
    ...   [ QueryCriterion('eq', 'username', 'tester'),
    ...     QueryCriterion('gt', 'balance', 50)
    ... ]).to_sql()
    "(username = 'tester' OR balance > 50)"
    '''
    @auto_set_fields
    def __init__(self, criteria):
        pass

    def to_sql(self):
        return "(%s)" % ' OR '.join([x.to_sql() for x in self.criteria])


# Function shared between InsertRows and SelectRows
def format_where_clause(crit):
    if crit:
        return 'WHERE %s' % crit.to_sql()
    else:
        return None

def make_order_by(by, desc):
    if by:
        ret = 'ORDER BY %s' % by
        if desc:
            return '%s DESC' % ret
        else:
            return ret
    else:
        assert desc is None, "Malformed order by, it only contains DESC value"
        return None

### Queries ###
class DeleteRows(Query):
    '''
    >>> print(DeleteRows('test_users', QueryCriterion('eq', 'username', 'test')).to_sql())
    DELETE FROM test_users
    WHERE username = 'test';
    '''
    @auto_set_fields
    def __init__(self, table_name, criteria, order_by=None, order_desc=None, limit=None):
        pass

    def to_sql(self):
        order_by_str = make_order_by(self.order_by, self.order_desc)

        return intercalate('\n',[
          'DELETE FROM %s' % self.table_name,
          'WHERE %s' % self.criteria.to_sql() if self.criteria else None,
          order_by_str,
          'LIMIT %d' % self.limit if self.limit else None,
        ]) + ';'


class UpdateRows(Query):
    '''
    >>> print(UpdateRows('test_users',
    ...   QueryCriterion('eq', 'username', 'tester'),
    ...   {'balance': 0, 'status':'broke'}
    ... ).to_sql())
    ...
    UPDATE test_users
    SET balance=0, status='broke'
    WHERE username = 'tester';
    '''
    @auto_set_fields
    def __init__(self, table_name, criteria, column_value_dict, order_by=None, order_desc=None, limit=None):
        # NOTE: doesn't really matter for this smart contracts, but orderby would be hel
        pass

    def to_sql(self):
        assignment_strs = ['%s=%s' % (k, cast_py_to_sql(v)) for (k,v) in self.column_value_dict.items()]
        order_by_str = make_order_by(self.order_by, self.order_desc)

        return intercalate('\n', [
          'UPDATE %s' % self.table_name,
          'SET %s' % intercalate(', ', assignment_strs),
          format_where_clause(self.criteria),
          order_by_str,
          'LIMIT %d' % self.limit if self.limit else None,
        ]) + ';'

# TODO: Change name to UpsertRows, see if this should actually be implemented with REPLACE
class SetRows(Query):
    # TODO: add unit test.
    # TODO: add query criterion and limit
    def __init__(self, table_name, list_of_values_lists):
        self.table_name = table_name
        # NOTE: Casting lists to tuples to ensure consistent types
        self.column_names = tuple(['k', 'v', 't'])
        self.list_of_values_lists = list(map(tuple, list_of_values_lists))

    def to_sql(self):
        correct_len = len(self.column_names)

        for idx, value_list in enumerate(self.list_of_values_lists):
            if len(self.list_of_values_lists[idx]) == correct_len - 1:
                self.list_of_values_lists[idx] = (*value_list, type(value_list[-1]).__name__)
            assert len(self.list_of_values_lists[idx]) == correct_len

        # NOTE: Given a list of rows, i.e. a list of lists, we take the the first
        # element of the list (a list representing a row). We use type info of
        # that first row to derrive type information
        casting_funcs = [get_py_to_sql_cast_func(type(x)) for x in self.list_of_values_lists[0]]

        def apply_funcs(xs):
            #''' Apply list of functions over a list of values '''
            #return [ f(x) for (f, x) in zip(casting_funcs, xs)]
            return map(cast_py_to_sql, xs)

        def format_string(xs):
            return '(%s)' % ', '.join(xs)

        def format_update(xs):
            return "v = %s" % list(xs)[1]

        convert_data_list_to_string = compose(format_string, apply_funcs)
        formatted_values_lists = [convert_data_list_to_string(x) for x in self.list_of_values_lists]
        convert_data_list_to_update = compose(format_update, apply_funcs)
        formatted_updates_lists = [convert_data_list_to_update(x) for x in self.list_of_values_lists]

        return '\n'.join([
          'INSERT INTO %s' % self.table_name,
          '(%s)' % ', '.join(self.column_names),
          'VALUES',
          ', '.join(formatted_values_lists),
          'ON DUPLICATE KEY UPDATE',
          ', '.join(formatted_updates_lists),
        ]) + ';'

class InsertRows(Query):
    '''
    >>> print(InsertRows('test_users', ['username', 'first_name', 'balance'],
    ...   [['tester', 'test', 500],
    ...    ['tester2', 'two', 200],
    ...   ]).to_sql())
    INSERT INTO test_users
    (username, first_name, balance)
    VALUES
    ('tester', 'test', 500), ('tester2', 'two', 200);
    '''
    def __init__(self, table_name, column_names, list_of_values_lists):
        self.table_name = table_name
        # NOTE: Casting lists to tuples to ensure consistent types
        self.column_names = tuple(column_names)
        self.list_of_values_lists = list(map(tuple, list_of_values_lists))


    def to_sql(self):
        correct_len = len(self.column_names)

        for value_list in self.list_of_values_lists:
            assert len(value_list) == correct_len

        # NOTE: Given a list of rows, i.e. a list of lists, we take the the first
        # element of the list (a list representing a row). We use type info of
        # that first row to derrive type information
        casting_funcs = [get_py_to_sql_cast_func(type(x)) for x in self.list_of_values_lists[0]]

        def apply_funcs(xs):
            #''' Apply list of functions over a list of values '''
            #return [ f(x) for (f, x) in zip(casting_funcs, xs)]
            return map(cast_py_to_sql, xs)

        def format_values(xs):
            return '(%s)' % ', '.join(xs)

        convert_data_list_to_string = compose(format_values, apply_funcs)
        formatted_values_lists = [convert_data_list_to_string(x) for x in self.list_of_values_lists]

        return '\n'.join([
          'INSERT INTO %s' % self.table_name,
          '(%s)' % ', '.join(self.column_names),
          'VALUES',
          ', '.join(formatted_values_lists),
        ]) + ';'


class SelectRows(Query):
    '''
    >>> print(SelectRows('test_users', [], None, None, None).to_sql())
    SELECT *
    FROM test_users;
    >>> print(SelectRows('test_users', [],
    ...  QueryCriterion('eq', 'username', 'tester'),
    ...  None,
    ...  None,
    ... ).to_sql())
    SELECT *
    FROM test_users
    WHERE username = 'tester';
    >>>
    >>> print(SelectRows('test_users', [],
    ...   QueryCriterion('gt', 'balance', 10),
    ...   None,
    ...   None,
    ... ).to_sql())
    SELECT *
    FROM test_users
    WHERE balance > 10;
    >>>
    >>> print(SelectRows('test_users', ['username', 'balance'],
    ...   QueryCriterion('gt', 'balance', 10),
    ...   None,
    ...   None,
    ... ).to_sql())
    SELECT username, balance
    FROM test_users
    WHERE balance > 10;
    >>>
    >>> print(SelectRows('test_users', ['username', 'balance'],
    ...   QueryCriterion('gt', 'balance', 10),
    ...   'balance',
    ...   None,
    ... ).to_sql())
    SELECT username, balance
    FROM test_users
    WHERE balance > 10
    ORDER BY balance;
    >>>
    >>> print(SelectRows('test_users', ['username', 'balance'],
    ...   QueryCriterion('gt', 'balance', 10),
    ...   limit=5,
    ... ).to_sql())
    SELECT username, balance
    FROM test_users
    WHERE balance > 10
    LIMIT 5;
    >>>
    >>> print(SelectRows('test_users', ['username', 'balance'],
    ...   QueryCriterion('gt', 'balance', 10),
    ...   'balance',
    ...   limit=5,
    ... ).to_sql())
    SELECT username, balance
    FROM test_users
    WHERE balance > 10
    ORDER BY balance
    LIMIT 5;
    '''

    # TODO: add orderby and limit
    @auto_set_fields
    def __init__(self,
                table_name,
                column_names,
                criteria,
                order_by=None,
                order_desc=None,
                limit=None):
        pass

    @staticmethod
    def format_column_names(c_names):
        if not c_names:
            # TODO: decide if we actually want this to auto-populate column names from python-side table object data instead
            return '*'
        else:
            return ', '.join(c_names)


    def to_sql(self):
        order_by_str = make_order_by(self.order_by, self.order_desc)

        return intercalate('\n', [
          'SELECT %s' % self.format_column_names(self.column_names),
          'FROM %s' % self.table_name,
          format_where_clause(self.criteria),
          order_by_str,
          'LIMIT %d' % self.limit if self.limit else None,
        ]) + ';'


class CountUniqueRows(Query):
    '''
    >>> print(CountUniqueRows('test_users', 'status', None).to_sql())
    SELECT status, COUNT(*) as _count
    FROM test_users
    GROUP BY status;

    >>> print(CountUniqueRows('test_users', 'status',
    ... QueryCriterion('eq', 'firstname', 'john')
    ... ).to_sql())
    SELECT status, COUNT(*) as _count
    FROM test_users
    WHERE firstname = 'john'
    GROUP BY status;
    '''
    @auto_set_fields
    def __init__(self, table_name, unique_column, criteria):
        pass

    def to_sql(self):
        return intercalate('\n', [
          'SELECT %s, COUNT(*) as _count' % self.unique_column,
          'FROM %s' % self.table_name,
          format_where_clause(self.criteria),
          'GROUP BY %s' % self.unique_column
        ]) + ';'


class CountRows(Query):
    '''
    >>> print(CountRows('test_users', None).to_sql())
    SELECT COUNT(*) as _count
    FROM test_users;

    >>> print(CountRows('test_users',
    ... QueryCriterion('eq', 'firstname', 'john')
    ... ).to_sql())
    SELECT COUNT(*) as _count
    FROM test_users
    WHERE firstname = 'john';
    '''
    @auto_set_fields
    def __init__(self, table_name, criteria):
        pass

    def to_sql(self):
        return intercalate('\n', [
          'SELECT COUNT(*) as _count',
          'FROM %s' % self.table_name,
          format_where_clause(self.criteria),
        ]) + ';'


class DescribeTable(Query):
    '''
    >>> print(DescribeTable('test_users').to_sql())
    DESCRIBE test_users;
    '''
    @auto_set_fields
    def __init__(self, table_name):
        pass

    def to_sql(self):
        return 'DESCRIBE %s;' % self.table_name


class ListTables(Query):
    '''
    >>> print(ListTables(None).to_sql())
    SHOW TABLES;
    >>> print(ListTables('tester_').to_sql())
    SHOW TABLES LIKE 'tester\_%;
    '''
    @auto_set_fields
    def __init__(self, prefix=None):
        pass

    @staticmethod
    def format_prefix(pf):
        if pf:
#            return 'LIKE \'%s\\_\%\'' % pf
            return 'LIKE \'{0}%'.format(escape_sql_pattern(pf))
        else:
            return None

    def to_sql(self):
        return intercalate(' ', [
            'SHOW TABLES',
            self.format_prefix(self.prefix),
        ]) + ';'



class AddTableColumn(Query):
    '''
    >>> print(AddTableColumn('test_users', ColumnDefinition('balance2', SQLType('BIGINT'), False)).to_sql())
    ALTER TABLE test_users
    ADD balance2 BIGINT;
    >>> print(AddTableColumn('test_users', ColumnDefinition('secondary_id', SQLType('VARCHAR', 30), True)).to_sql())
    ALTER TABLE test_users
    ADD secondary_id VARCHAR(30) UNIQUE;
    '''
    @auto_set_fields
    def __init__(self, table_name, column_def):
        pass

    def to_sql(self):
        #name, sql_type, is_unique
        return intercalate('\n',[
          'ALTER TABLE %s' % self.table_name,
          'ADD %s' % self.column_def.to_sql()
        ]) + ';'


class DropTableColumn(Query):
    '''
    >>> print(DropTableColumn('test_users', 'balance2').to_sql())
    ALTER TABLE test_users
    DROP COLUMN balance2;
    '''
    @auto_set_fields
    def __init__(self, table_name, column_name):
        pass

    def to_sql(self):
        return intercalate('\n', [
          'ALTER TABLE %s' % self.table_name,
          'DROP COLUMN %s' % self.column_name
        ]) + ';'


class DropTable(Query):
    '''
    >>> print(DropTable('test_users').to_sql())
    DROP TABLE test_users;
    '''
    @auto_set_fields
    def __init__(self, table_name):
        pass

    def to_sql(self):
        return 'DROP TABLE %s;' % self.table_name


class CreateTable(Query):
    '''
    >>> print(CreateTable(
    ...       'test_users',
    ...       AutoIncrementColumn('id'),
    ...       [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
    ...         ColumnDefinition('drivers_licence_unmber', SQLType('VARCHAR', 30), True),
    ...         ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
    ...         ColumnDefinition('balance', SQLType('BIGINT'), False),
    ... ]).to_sql())
    CREATE TABLE test_users (
    id BIGINT unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) UNIQUE,
    drivers_licence_unmber VARCHAR(30) UNIQUE,
    first_name VARCHAR(30),
    balance BIGINT
    );

    >>> print(CreateTable(
    ...       'test_users',
    ...       AutoIncrementColumn('id'),
    ...       [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
    ...         ColumnDefinition('drivers_licence_unmber', SQLType('VARCHAR', 30), True),
    ...         ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
    ...         ColumnDefinition('balance', SQLType('BIGINT'), False),
    ... ], if_not_exists=True).to_sql())
    CREATE TABLE IF NOT EXISTS test_users (
    id BIGINT unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) UNIQUE,
    drivers_licence_unmber VARCHAR(30) UNIQUE,
    first_name VARCHAR(30),
    balance BIGINT
    );
    '''
    @auto_set_fields
    def __init__(self, table_name, primary_key_column_def, other_column_defs, if_not_exists=False):
        #print(self.__dict__)
        pass

    def to_sql(self):
        column_def_strs = (
          [self.primary_key_column_def.to_sql() + ' PRIMARY KEY'] +
          list(map(lambda x: x.to_sql(), self.other_column_defs))
        )

        ine = 'IF NOT EXISTS' if self.if_not_exists else ''

        return '\n'.join([
          'CREATE TABLE %s (' % intercalate(' ', [ine, self.table_name]),
          intercalate(',\n', column_def_strs),
          ');'
        ])


def run_tests(_):
    '''
    >>> NonNullableBooleanColumn('test').to_sql()
    'test Boolean NOT NULL DEFAULT FALSE'
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__])
