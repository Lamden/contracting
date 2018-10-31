'''
# Simple tabular datastore #
* Uses myrocks to support SQL operations on rocksdb
* Right now relying on yet to be built execution environment to force squential evaluation of contracts
  * Not doing any concurrency control/transactions. Consistency maintained by that sequential evaluation

* Tabular2
  * When delete column, delete from table object
  * have to change the way we auto increment id, has to be compatible with rollback
  * Works with both mysql-base and mysql-pit

*TODOs
  * upsert, i.e. ON DUPLICATE KEY UPDATE
  * list tables
  * Type annotations
'''

from itertools import zip_longest
import warnings
import datetime
from datetime import datetime, timedelta

from seneca.engine.util import auto_set_fields, add_methods, add_method_as, filter_split, assert_len
import seneca.engine.storage.mysql_intermediate as isql
from seneca.engine.storage.mysql_base import FixedStr, cast_py_to_sql
#from inflection import  underscore, camelize

# Convenience functions for dealing with lists, dicts, and objects
def m_subscript(sub_able, sub):
    '''Maybe subscript, if a subscript exists at the specified index or key, it
    will be returned, else, None will be returned, errors are suppressed.'''
    try:
        return sub_able[sub]
    except (IndexError, KeyError) as e:
        return None


def m_getattr(sub_able, sub):
    '''Maybe getattr, if an attr exists it will be returned, else, None will be
    returned, errors are suppressed.'''
    try:
        return getattr(sub_able, sub)
    except AttributeError as e:
        return None


def get_exactly_one(xs):
    assert_len(1, xs)
    return xs[0]


def filter_type(xs, t):
    return [x for x in xs if type(x) == t]


def table_name_from_cs(cs):
    return require_from_cs(cs, Table, 'sql_name')()


def optional_from_cs(stack, type_, attr):
    return m_getattr(m_subscript(filter_type(stack, type_), 0), attr)


def require_from_cs(cs, t, attr):
    return getattr(get_exactly_one(filter_type(cs, t)), attr)


def str_len(l):
    '''Type constructor function, made to look like builtin str()'''
    return FixedStr.Len(l)


### Shared methods, added to classes via decorator, treated like single-method traits ###
def where(self, where_criterion):
    return WhereClause(self.call_stack.copy(), where_criterion)


def order_by(self, order_by_column_name, desc=False):
    return OrderBy(self.call_stack.copy(), order_by_column_name, desc=desc)


def limit(self, count_limit):
    return LimitTo(self.call_stack.copy(), count_limit)


def terminal_where(self, where_criterion):
    # A where clause without order_by or limit, effective terminates choices in call chain (only .run)
    return TerminalWhereClause(self.call_stack.copy(), where_criterion)
# End of single-method traits


def execute_sql_query(executer, isql_obj):
    res = executer(isql_obj)

    if not res.success:
        raise Exception(res.data)
    else:
        return res.data


class Column(object):
    @auto_set_fields
    def __init__(self, name, type=None, unique=False):
        pass

    # Custom methods make the results of comparisons in query components
    # e.g (Column('some_column') != None).to_sql() -> 'some_column IS NOT NULL'
    def __eq__(self, other):
        return isql.QueryCriterion('eq', self.name, other)

    def __ne__(self, other):
        return isql.QueryCriterion('ne', self.name, other)

    def __lt__(self, other):
        return isql.QueryCriterion('lt', self.name, other)

    def __gt__(self, other):
        return isql.QueryCriterion('gt', self.name, other)

    def __le__(self, other):
        return isql.QueryCriterion('le', self.name, other)

    def __ge__(self, other):
        return isql.QueryCriterion('ge', self.name, other)

    def to_intermediate_def(self):
        # TODO: Change this into a proper raise of custom exception class
        assert self.type, "When defining table column, a type must be declared"
        sql_type = isql.SQLType.from_python_type(self.type)

        return isql.ColumnDefinition(self.name, sql_type, unique=self.unique)

    @classmethod
    def from_sql_describe_row(cls, row):
        '''Alternate constructor: Instead of constructing from user provided
        parameters, it runs a DESCRIBE <TABLE>; query, and construct Column from
        the data it gets back.'''

        # XXX: This may break if sql is updated or maria vs mysql, or something
        name = row['Field']

        if row['Type'].lower() == 'bigint(20) unsigned' and \
                     row['Extra'].lower() == 'auto_increment':
            return AutoIncrementColumn(name)
        else:
            type_ = isql.SQLType.from_db_describe_str(row['Type'])
            unique = row['Key'].lower() == 'uni'
            return cls(name, type=type_, unique=unique)


class AutoIncrementColumn(Column):
    '''Special instance of Column with automatically incrementing bigint,
    intended for use as primary keys.'''
    @auto_set_fields
    def __init__(self, name):
        pass

    def to_intermediate_def(self):
        return isql.AutoIncrementColumn(self.name)


def and_(*args):
    '''Function constructs compound where clauses, matches SQLAlchemy API.'''
    return isql.AndedCriteria(args)

def not_(c):
    '''Function negates where clauses, matches SQLAlchemy API.'''
    return isql.InvertedCriterion(c)

def or_(*args):
    '''Function constructs compound where clauses, matches SQLAlchemy API.'''
    return isql.OredCriteria(args)


# NOTE: The following classes are used to build sql-like method chains. They
# each represent a destinct part of an SQL query. When chained, they follow the
# same rules as real SQL regarding syntax and order of operations e.g.
# 'order by' cannot come before 'where'.
# Different parts of SQL must be in order and are often optional (i.e.
# not required), e.g. 'where ...', 'order by', 'limit'. Generally speaking,
# these classes each have an ever narrowing set of available methods, e.g.
# select may be followed by .where(), order_by(), limit(), or run(), but
# .order_by(...) may only be followed by .limit() and .run() methods available,
# per SQL syntax, .where() would have had to come before order_by(). In contrast
# .select() will return an object with all previously mentioned methods available.
class QueryComponent(object):
    '''Base class for sql method chains.'''
    def __init__(self, call_stack, *args, **kwargs):
        self.call_stack = call_stack
        self.call_stack.append(self)
        self._supplemental_init(*args, **kwargs)

    def _supplemental_init(self, *args, **kwargs):
        '''Many constructor for sql methods have special arguments and behaviors.
        Structuring init in 2 functions allows classes to inherit and use a common
        __init__ to handle the callstack, but still have unique supplemental
        behaviors layered on top.'''
        pass


    def to_isql(self):
        ''' This method starts the process of unwinding the method chain
        callstack, it finds the sql verb (e.g. select(), update(), insert(), or
        delete()), does some light validation, then uses the verb's
        to_intermediate to turn the entire callstack into a representation of a
        SQL query.'''
        tlqcs = [x for x in self.call_stack if issubclass(type(x), SQLVerb)]
        assert_len(1, tlqcs) # There should only ever be one method/verb per query.
        sql_verb = tlqcs[0]
        # The SQL method/verb is the only query component type that can generate
        # a representation of the query
        return sql_verb.to_intermediate(self.call_stack)

    def run(self, ex):
        return execute_sql_query(ex, self.to_isql())

    def to_sql(self):
        return self.to_isql().to_sql()

    def __str__(self):
        d1 = self.__dict__.copy()
        d1.pop('call_stack')
        return '%s(%s)' % (type(self).__name__, str(d1))

    def __repr__(self):
        return self.__str__()


class LimitTo(QueryComponent):
    ''' Limit must be the last statement in our standard SQL queries, it
    inherits the .run() method from QueryComponent, and can't do anything else.
    '''
    @auto_set_fields
    def _supplemental_init(self, count_limit):
        # TODO: Validate count_limit value
        pass


class TerminalWhereClause(QueryComponent):
    '''Simplified where clause that doesn't have any methods except .run() so
    it effectively ends the chain of methods.'''
    @auto_set_fields
    def _supplemental_init(self, where_criterion):
        # TODO: Validate where_criterion value
        pass


@add_methods(limit)
class OrderBy(QueryComponent):
    @auto_set_fields
    def _supplemental_init(self, column_name, desc=False):
        pass


@add_methods(limit, order_by)
class WhereClause(QueryComponent):
    @auto_set_fields
    def _supplemental_init(self, where_criterion):
        #TODO: Verify not empty
        pass


class SQLVerb(QueryComponent):
    ''' Abstract class, todo, use ABC and @abstractmethod '''
    @auto_set_fields
    def _supplemental_init(self, *where_criteria):
        raise NotImplementedError("Class should never be instantiated")


# This verb has run() but no other chainable methods.
class AddTableColumn(SQLVerb):
    @auto_set_fields
    def _supplemental_init(self, column_def):
        pass

    def to_intermediate(self, full_call_stack):
        table_name = table_name_from_cs(full_call_stack)
        isql_column_def = self.column_def.to_intermediate_def()

        return isql.AddTableColumn(table_name, isql_column_def)


class DropTableColumn(SQLVerb):
    @auto_set_fields
    def _supplemental_init(self, column_name):
        pass

    def to_intermediate(self, full_call_stack):
        # TODO: Dedupe this section from other Classes. Ideally with __lt__ implemented for automatic sorting.
        # and individual to_intermediate methods for all classes so just sort and map that over list.
        table_name = table_name_from_cs(full_call_stack)
        column_name = require_from_cs(full_call_stack, DropTableColumn, 'column_name')

        return isql.DropTableColumn(table_name, column_name)


@add_method_as(terminal_where, 'where')
class CountRows(SQLVerb):
    # Overwrite supplemental with noop
    def _supplemental_init(self, *args):
        pass

    def to_intermediate(self, call_stack):
        # TODO: Dedupe this section from other Classes. Ideally with __lt__ implemented for automatic sorting.
        table_name = table_name_from_cs(call_stack)
        criterion = optional_from_cs(call_stack, TerminalWhereClause, 'where_criterion')
        return isql.CountRows(table_name, criterion)


@add_method_as(terminal_where, 'where')
class CountUniqueRows(SQLVerb):
    @auto_set_fields
    def _supplemental_init(self, column_name):
        pass

    def to_intermediate(self, call_stack):
        # TODO: Dedupe this section from other Classes. Ideally with __lt__ implemented for automatic sorting.
        # and individual to_intermediate methods for all classes so just sort and map that over list.
        table_name = table_name_from_cs(call_stack)
        unique_column_name = require_from_cs(call_stack, CountUniqueRows, 'column_name')
        criterion = optional_from_cs(call_stack, TerminalWhereClause, 'where_criterion')
        return isql.CountUniqueRows(table_name, unique_column_name, criterion)


@add_methods(where, order_by, limit)
class DeleteRows(SQLVerb):
    # Overwrite supplemental with noop
    def _supplemental_init(self, *args):
        pass

    def to_intermediate(self, full_call_stack):
        table_name = table_name_from_cs(full_call_stack)
        criterion = optional_from_cs(full_call_stack, WhereClause, 'where_criterion')
        order_by = optional_from_cs(full_call_stack, OrderBy, 'column_name')
        order_desc = optional_from_cs(full_call_stack, OrderBy, 'desc')
        limit = optional_from_cs(full_call_stack, LimitTo, 'count_limit')
        return isql.DeleteRows(table_name,
                               criterion,
                               order_by=order_by,
                               order_desc=order_desc,
                               limit=limit)

class InsertRows(SQLVerb):
    @auto_set_fields
    def _supplemental_init(self, list_column_val_dicts):
        pass

    @staticmethod
    def to_intermediate(full_call_stack):
        table_name = table_name_from_cs(full_call_stack)
        list_column_val_dicts = require_from_cs(full_call_stack, InsertRows, 'list_column_val_dicts')
        tab_kv = isql.TabularKVs.from_dicts(list_column_val_dicts)
        return isql.InsertRows(table_name, *tab_kv.to_klist_vlists())


@add_methods(where, order_by, limit)
class UpdateRows(SQLVerb):
    @auto_set_fields
    def _supplemental_init(self, column_val_dict):
        pass

    @staticmethod
    def to_intermediate(full_call_stack):
        table_name = table_name_from_cs(full_call_stack)
        column_value_dict = require_from_cs(full_call_stack, UpdateRows, 'column_val_dict')
        criterion = optional_from_cs(full_call_stack, WhereClause, 'where_criterion')
        order_by = optional_from_cs(full_call_stack, OrderBy, 'column_name')
        order_desc = optional_from_cs(full_call_stack, OrderBy, 'desc')
        limit = optional_from_cs(full_call_stack, LimitTo, 'count_limit')

        return isql.UpdateRows(table_name,
                               criterion,
                               column_value_dict,
                               order_by=order_by,
                               order_desc=order_desc,
                               limit=limit)

class SetRows(SQLVerb):
    @auto_set_fields
    def _supplemental_init(self, column_val_list):
        pass

    @staticmethod
    def to_intermediate(full_call_stack):
        table_name = table_name_from_cs(full_call_stack)
        column_val_list = require_from_cs(full_call_stack, SetRows, 'column_val_list')
        return isql.SetRows(table_name, column_val_list)


@add_methods(where, order_by, limit)
class SelectRows(SQLVerb):
    def _supplemental_init(self, *field_names):
        self.field_names = list(field_names)

    @staticmethod
    def to_intermediate(full_call_stack):
        table_name = table_name_from_cs(full_call_stack)
        column_names = optional_from_cs(full_call_stack, SelectRows, 'field_names')
        criterion = optional_from_cs(full_call_stack, WhereClause, 'where_criterion')
        order_by = optional_from_cs(full_call_stack, OrderBy, 'column_name')
        order_desc = optional_from_cs(full_call_stack, OrderBy, 'desc')
        limit = optional_from_cs(full_call_stack, LimitTo, 'count_limit')
        return isql.SelectRows(table_name,
                               column_names,
                               criterion,
                               order_by=order_by,
                               order_desc=order_desc,
                               limit=limit)


class Table(object):
    # TODO: create conveniently with id field already specced
    def __init__(self, name, primary_column, other_columns):
        self.call_stack = [self]
        self._name = name
        self.primary_key_column = primary_column
        self.other_columns = other_columns

        native_fields = set(dir(self))
        if primary_column:
            all_columns = [primary_column] + other_columns
        else:
            all_columns = other_columns
        column_names = set(map(lambda x: x.name, all_columns))

        namespace_conflicts = native_fields & column_names
        assert not namespace_conflicts, 'A forbidden column name has been used.'

        for c in all_columns:
            setattr(self, c.name, c)

    @classmethod
    def from_existing(cls, name):
        def run(ex):
            # TODO: return runable
            column_descriptions = execute_sql_query(ex, isql.DescribeTable(name))

            # Find primary key column and separate from others
            pkey_col_dict_list, other_cols_dict_list = \
              filter_split(lambda r: r['Key'].upper() == 'PRI', column_descriptions)
            if len(pkey_col_dict_list) == 0:
                pkey_col = None
            elif len(pkey_col_dict_list) == 1:
                pkey_col = Column.from_sql_describe_row(pkey_col_dict_list[0])
            else:
                raise Exception("Error, there should only every be one primary key column description")

            return cls(name,
                       pkey_col,
                       [Column.from_sql_describe_row(x) for x in other_cols_dict_list]
                       )

        return SimpleRunnable(run)


    def sql_name(self):
        #TODO: Implement this
        return self._name

    def insert(self, data):
        return InsertRows(self.call_stack.copy(), data)

    def select(self, *field_names):
        return SelectRows(self.call_stack.copy(), *field_names)

    def update(self, column_val_dict):
        return UpdateRows(self.call_stack.copy(), column_val_dict)

    def set(self, column_val_dict):
        return SetRows(self.call_stack.copy(), column_val_dict)

    def get(self, field_name):
        return self.select('v', 't').where(self.k == field_name)

    def delete(self):
        return DeleteRows(self.call_stack.copy())

    def count(self):
        return CountRows(self.call_stack.copy())

    def count_unique(self, column_name):
        return CountUniqueRows(self.call_stack.copy(), column_name)

    def add_column(self, *args, **kwargs):
        column_def = Column(*args, **kwargs)
        return AddTableColumn(self.call_stack.copy(), column_def)

    def drop_column(self, column_name):
        return DropTableColumn(self.call_stack.copy(), column_name)

    def __str__(self):
        d1 = self.__dict__.copy()
        d1.pop('call_stack')
        return '%s(%s)' % (type(self).__name__, str(d1))

    def __repr__(self):
        return self.__str__()

    def _to_intermediate_create(self, if_not_exists):
        return isql.CreateTable(self._name,
                                self.primary_key_column.to_intermediate_def(),
                                list(map(
                                  lambda x: x.to_intermediate_def(),
                                  self.other_columns
                                )),
                                if_not_exists=if_not_exists
                               )

    def create_table(self, if_not_exists=False):
        return RunnableISQL(self._to_intermediate_create(if_not_exists))

    def _to_intermediate_drop(self):
        return isql.DropTable(self._name)

    def drop_table(self):
        # TODO: if exists
        return RunnableISQL(self._to_intermediate_drop())


class SimpleRunnable(object):
    ''' Bare bones class with run method.
    '''
    @auto_set_fields
    def __init__(self, run_func):
        pass

    def run(self, *args, **kwargs):
        return self.run_func(*args, **kwargs)


class RunnableISQL(object):
    @auto_set_fields
    def __init__(self, isql, results_parser=lambda x:x):
        pass

    def to_isql(self):
        return self.isql

    def run(self, ex):
        return self.results_parser(execute_sql_query(ex, self.isql))

    def to_sql(self):
        return self.isql.to_sql()


def run_tests(deps_provider):
    '''
    TODO: Tests to validate interface of return values from update, select, etc.
    TODO: Decide whether or not object properties can be passed to select like strings

    >>> u = Table('users', AutoIncrementColumn('id'),[
    ...    Column('first_name', str),
    ...    Column('last_name', str),
    ...    Column('balance', int),
    ...    Column('creation_date', datetime)
    ... ])

    >>> u.create_table(if_not_exists=False).run(ex)
    >>> x = u.select().where(u.first_name != None).run(ex)
    >>> type(x) == TabularKVs
    True
    >>> len(x) == 0
    True

    >>> _ = u.insert([
    ...  {'first_name': 'Test', 'last_name': 'User','balance': 10},
    ...  {'first_name': 'Test2', 'last_name': 'User','balance': 20},
    ...  {'first_name': 'Test3', 'last_name': 'User','balance': 30},
    ... ]).run(ex)

    >>> print(repr(u.select().run(ex)))
    {'id': 1, 'first_name': 'Test', 'last_name': 'User', 'balance': 10, 'creation_date': None}
    {'id': 2, 'first_name': 'Test2', 'last_name': 'User', 'balance': 20, 'creation_date': None}
    {'id': 3, 'first_name': 'Test3', 'last_name': 'User', 'balance': 30, 'creation_date': None}


    # Test ordering of select
    >>> u.select('id', 'first_name').order_by('id', desc=True).run(ex)
    {'id': 3, 'first_name': 'Test3'}
    {'id': 2, 'first_name': 'Test2'}
    {'id': 1, 'first_name': 'Test'}

    # Test counts
    >>> u.count().run(ex)
    3
    >>> u.count().where(u.first_name == 'Test2').run(ex)
    1
    >>> u.count().where(u.first_name != 'Test2').run(ex)
    2

    # Test count uniques
    >>> u.count_unique('first_name').run(ex)
    {'first_name': 'Test', '_count': 1}
    {'first_name': 'Test2', '_count': 1}
    {'first_name': 'Test3', '_count': 1}


    # Test full update of all rows
    >>> _ = u.update({'balance': 1000}).run(ex)
    >>> print(repr(u.select('balance').run(ex)))
    {'balance': 1000}
    {'balance': 1000}
    {'balance': 1000}


    # Modify columns
    >>> u.add_column('nick_name', str).run(ex)
    >>> u.add_column('unique_nick_name', str_len(30), True).run(ex)
    >>> u.select('nick_name', 'unique_nick_name').run(ex)
    {'nick_name': None, 'unique_nick_name': None}
    {'nick_name': None, 'unique_nick_name': None}
    {'nick_name': None, 'unique_nick_name': None}

    # TODO: test to make sure unique is enforced

    # Test a delete, where clause, and an or_
    >>> _ = u.delete().where(
    ...    or_(
    ...        u.first_name == 'Test',
    ...        Column('first_name') == 'Test3'
    ...    )
    ... ).run(ex)
    >>> u.select('first_name').run(ex)
    {'first_name': 'Test2'}

    # Test pull existing table by name
    >>> t2 = Table.from_existing('users').run(ex)
    >>> t2.select('first_name').run(ex)
    {'first_name': 'Test2'}
    '''
    import doctest, sys
    from seneca.engine.storage.mysql_executer import Executer
    from seneca.engine.storage.mysql_base import TabularKVs

    ex = deps_provider(Executer)

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
