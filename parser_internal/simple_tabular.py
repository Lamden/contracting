'''
# Simple tabular datastore #
* Uses myrocks to support SQL operations on rocksdb
* Right now relying on yet to be built execution environment to force squential evaluation of contracts
  * Not doing any concurrency control/transactions. Consistency maintained by that sequential evaluation

* Tabular2
  * When delete column, delete from table object
  * have to change the way we auto increment id, has to be compatible with rollback
  * Works with both mysql-base and mysql-pit
'''

# TODO: proper table constructor, create_table, get_table, table_name-to-sql
# TODO: dedupe code
# TODO: make names of conversion functions uniform so it's easy to see where they are and add new types
# TODO: configurable verbosity
# TODO: verify this is being called each time it's imported.

from itertools import zip_longest
from util import auto_set_fields
import warnings
import datetime
import mysql_queries as isql
from datetime import datetime, timedelta
#from inflection import  underscore, camelize
'''
TODOS:
static methods:

get_table()
create_table()
drop_table()
run_batch()
add_column()
drop_column()

outside_table
run_batch
str_len
create_table
drop_table,
add_column,
drop_column,

u = create_table('users', [
    ('first_name', str_len(30), True),
    ('last_name', str_len(30), True),
    ('nick_name', str_len(30)),
    ('balance', int)
])
'''

def fallback_executer(query):
    print('> No executer has been provided, echoing query:\n%s\n' % query)


def runner(f):
    def wrap(obj_self, *args):
        isql_obj = f(obj_self)

        if len(args) == 0:
            fallback_executer(isql_obj.to_sql())
        elif len(args) == 1:
            executer = args[0]
            res = executer(isql_obj)
            if not res.success:
                raise Exception(res.data)
            else:
                return res.data
        else:
            raise TypeError("Too many arguments. 0 or 1 args + self allowed.")

    return wrap

# TODO: dedupe with runner()
def static_runner(f):
    def wrap(*args):
        isql_obj = f()

        if len(args) == 0:
            fallback_executer(isql_obj.to_sql())
        elif len(args) == 1:
            executer = args[0]
            res = executer(isql_obj)
            if not res.success:
                raise Exception(res.data)
            else:
                return res.data
        else:
            raise TypeError("Too many arguments. 0 or 1 args + self allowed.")

    return wrap



class Column(object):
    @auto_set_fields
    def __init__(self, name, type=None, unique=False, nullable=True):
        pass

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
        assert self.type, "When defining table column, a type must be declared"
        sql_type = isql.py_mysql_dict[self.type]

        return isql.ColumnDefinition(self.name, sql_type, unique=self.unique, nullable=self.nullable)


class AutoIncrementColumn(Column):
    @auto_set_fields
    def __init__(self, name):
        pass

    def to_intermediate_def(self):
        return isql.AutoIncrementColumn(self.name)


def and_(*args):
    return isql.AndedCriteria(args)

def not_(c):
    return isql.InvertedCriterion(c)

def or_(*args):
    return isql.OredCriteria(args)


class QueryComponent(object):
    def __init__(self, call_stack, *args, **kwargs):
        self.call_stack = call_stack
        self.call_stack.append(self)
        self._supplemental_init(*args, **kwargs)

    def _supplemental_init(self, *args, **kwargs):
        pass

    @runner
    def run(self):
        # Get the top level query component, a SQL method (select, update, etc.)
        tlqcs = [x for x in self.call_stack if issubclass(type(x), TopLevelQueryComponent)]
        ensure_len(1, tlqcs) # There should only ever be one method/verb per query.
        sql_verb = tlqcs[0]
        # The SQL method/verb is the only query component that can generate a full
        # Intermediate representation of the query.
        inter = sql_verb.to_intermediate(self.call_stack)
        return inter


    def __str__(self):
        d1 = self.__dict__.copy()
        d1.pop('call_stack')
        return '%s(%s)' % (type(self).__name__, str(d1))

    def __repr__(self):
        return self.__str__()


class LimitTo(QueryComponent):
    @auto_set_fields
    def _supplemental_init(self, count_limit):
        pass


class OrderBy(QueryComponent):
    @auto_set_fields
    def _supplemental_init(self, column_name, desc=False):
        pass

    def limit(self, count_limit):
        return LimitTo(self.call_stack.copy(), count_limit)


class WhereClause(OrderBy):
    @auto_set_fields
    def _supplemental_init(self, where_criterion):
        #TODO: Verify not empty
        pass

    def order_by(self, order_by_column_name, desc=False):
        return OrderBy(self.call_stack.copy(), order_by_column_name, desc=desc)


class TopLevelQueryComponent(WhereClause):
    @auto_set_fields
    def _supplemental_init(self, *where_criteria):
        raise NotImplementedError("Class should never be instantiated")

    def where(self, where_criterion):
        return WhereClause(self.call_stack.copy(), where_criterion)

def safe_list_accessor(xs, i):
    try:
        return xs[i]
    except IndexError:
        return None

def safe_getattr(obj, attr_name):
    if obj is None:
        return None
    else:
        return getattr(obj, attr_name)

def safe_dict_accessor(d, k):
    if d is None:
        return None
    else:
        return d[k]

def filter_type(t, xs):
    return [x for x in xs if type(x) == t]

def ensure_len(l, xs):
    assert len(xs) == l, str(xs)

def get_qc(t, xs):
    xs_f = filter_type(t, xs)
    return safe_list_accessor(xs_f, 0)


class DeleteRows(TopLevelQueryComponent):
    # Overwrite supplemental with noop
    def _supplemental_init(self, *args):
        pass

    def to_intermediate(self, full_call_stack):
        table_name = get_qc(Table, full_call_stack).sql_name()
        criterion = safe_getattr(get_qc(WhereClause, full_call_stack), 'where_criterion') #TODO: Implement this
        order_by = safe_getattr(get_qc(OrderBy, full_call_stack), 'column_name')
        order_desc = safe_getattr(get_qc(OrderBy, full_call_stack), 'desc')
        limit = safe_getattr(get_qc(LimitTo, full_call_stack), 'count_limit')
        return isql.DeleteRows(table_name,
                               criterion,
                               order_by=order_by,
                               order_desc=order_desc,
                               limit=limit)


class InsertRows(TopLevelQueryComponent):
    @auto_set_fields
    def _supplemental_init(self, list_column_val_dicts):
        pass

    @staticmethod
    def to_intermediate(full_call_stack):
        table_name = get_qc(Table, full_call_stack).sql_name()
        list_column_val_dicts = safe_getattr(get_qc(InsertRows, full_call_stack), 'list_column_val_dicts')

        tab_kv = isql.TabularKVs.from_dicts(list_column_val_dicts)
        return isql.InsertRows(table_name, *tab_kv.to_klist_vlists())


class UpdateRows(TopLevelQueryComponent):
    @auto_set_fields
    def _supplemental_init(self, column_val_dict):
        pass

    @staticmethod
    def to_intermediate(full_call_stack):
        table_name = get_qc(Table, full_call_stack).sql_name()
        criterion = safe_getattr(get_qc(WhereClause, full_call_stack), 'where_criterion') #TODO: Implement this
        column_value_dict = safe_getattr(get_qc(UpdateRows, full_call_stack), 'column_val_dict')
        order_by = safe_getattr(get_qc(OrderBy, full_call_stack), 'column_name')
        order_desc = safe_getattr(get_qc(OrderBy, full_call_stack), 'desc')
        limit = safe_getattr(get_qc(LimitTo, full_call_stack), 'count_limit')

        return isql.UpdateRows(table_name,
                               criterion,
                               column_value_dict,
                               order_by=order_by,
                               order_desc=order_desc,
                               limit=limit)


class SelectRows(TopLevelQueryComponent):
    def _supplemental_init(self, *field_names):
        self.field_names = list(field_names)

    @staticmethod
    def to_intermediate(full_call_stack):
        table_name = get_qc(Table, full_call_stack).sql_name()
        column_names = safe_getattr(get_qc(SelectRows, full_call_stack), 'field_names')
        criterion = safe_getattr(get_qc(WhereClause, full_call_stack), 'where_criterion') #TODO: Implement this
        order_by = safe_getattr(get_qc(OrderBy, full_call_stack), 'column_name')
        order_desc = safe_getattr(get_qc(OrderBy, full_call_stack), 'desc')
        limit = safe_getattr(get_qc(LimitTo, full_call_stack), 'count_limit')
        return isql.SelectRows(table_name,
                               column_names,
                               criterion,
                               order_by=order_by,
                               order_desc=order_desc,
                               limit=limit)


class Table(object):
    # TODO: 3 types of instantiation
    # * get existing from database
    # * create with full column spec (including primary key column)
    # * create conveniently with id field already specced
    def __init__(self, name, primary_column, other_columns):
        self.call_stack = [self]
        self._name = name
        self.primary_key_column = primary_column
        self.other_columns = other_columns

        native_fields = set(dir(self))
        all_columns = [primary_column] + other_columns
        column_names = set(map(lambda x: x.name, all_columns))

        namespace_conflicts = native_fields & column_names
        assert not namespace_conflicts, 'A forbidden column name has been used.'

        for c in all_columns:
            setattr(self, c.name, c)


    def sql_name(self):
        #TODO: Implement this
        return self._name

    def insert(self, data):
        return InsertRows(self.call_stack.copy(), data)

    def select(self, *field_names):
        return SelectRows(self.call_stack.copy(), *field_names)

    def update(self, column_val_dict):
        return UpdateRows(self.call_stack.copy(), column_val_dict)

    def delete(self):
        return DeleteRows(self.call_stack.copy())

    def __str__(self):
        d1 = self.__dict__.copy()
        d1.pop('call_stack')
        return '%s(%s)' % (type(self).__name__, str(d1))


    def __repr__(self):
        return self.__str__()

    def _to_intermediate_create(self, if_not_exists=False):
        return isql.CreateTable(self._name,
                                self.primary_key_column.to_intermediate_def(),
                                list(map(
                                  lambda x: x.to_intermediate_def(),
                                  self.other_columns
                                )),
                                if_not_exists=if_not_exists
                               )

    def _to_itermediate_drop(self):
        return isql.DropTable(self._name)


class SimpleRunnable():
    @auto_set_fields
    def __init__(self, run):
        pass

    def run(*args, **kwargs):
        return self.run(*args, **kwargs)


def create_table_query(table, if_not_exists=False):
    return SimpleRunnable(static_runner(
        lambda : table._to_intermediate_create(if_not_exists=if_not_exists)
    ))

def drop_table_query(table):
    return SimpleRunnable(static_runner(
        lambda : table._to_itermediate_drop()
    ))


if __name__ == '__main__':
    import sys
    from mysql_executer import Executer

    ex_ = Executer('seneca_test', sys.argv[1], 'seneca_test', '127.0.0.1')

    def ex(obj):
        print('Running Query:')
        print(obj.to_sql())
        res = ex_(obj)
        print(res)
        print('\n')
        return res

    u = Table('users', AutoIncrementColumn('id'),[
        Column('first_name', str),
        Column('last_name', str),
        Column('balance', int),
        Column('creation_date', datetime)
    ])
    try:
        drop_table_query(u).run(ex)
    except Exception as e:
        print(e)
    create_table_query(u, if_not_exists=True).run(ex)

    u.insert([
      {'first_name': 'Test', 'last_name': 'User','balance': 0},
      {'first_name': 'Test2', 'last_name': 'User','balance': 0},
      {'first_name': 'Test3', 'last_name': 'User','balance': 0},
    ]).run(ex)
    print(u.select().run(ex))

    u.update({'balance': 1000}).run(ex)
    print(u.select().run(ex))

    print(u.select('id', 'first_name').order_by('id', desc=True).run(ex))

    u.delete().where(
        or_(
            Column('first_name') == 'Test',
            Column('first_name') == 'Test3'
        )
    ).run(ex)

    print(u.select().run(ex))
