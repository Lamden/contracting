'''
# Simple tabular datastore #
* Uses myrocks to support SQL operations on rocksdb
* Right now relying on yet to be built execution environment to force squential evaluation of contracts
  * Not doing any concurrency control/transactions. Consistency maintained by that sequential evaluation
* Implementing prototype with SQL alchemy

* Must start work on Seneca import system so we can inject caller address here.
  * Must not be a singleton like standard Python imports because it's very possible this lib will be called by multiple smart contracts in chain and need to give each its own instance
  * Alternatively, it could just always pass smart_contract_id as first arg
  * Caller could just be injected as module-global var

* Need a way tie all mutations smart contract address of caller
  * Probably do not want this for data access

* Maybe provide a transaction interface for performance (or if some kind of parallel execution is eventually allowed.)


* Note: currently no foreign keys allowed in Myrocks, this is a feature under development so we may want to add it when they do.


* Big TODOs:
  * Make this secure. Serialized requests to a separate process, and validate before running based on caller.
  * Do we allow joins across smart contracts? Peformance implications for sure. Will limit future architecture possibilities
  *


'''



# TODO: verify this is being called each time it's imported.
#print("loading tabular, TODO: make sure this loads for each and every import")
#print("caller: %s" % seneca_internal.smart_contract_caller)

from itertools import zip_longest
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Sequence, select
import MySQLdb

# TODO: figure out how we want to handle these.
METADATA = MetaData()
# TODO: Replace this with the real engine from Cilantro


# TODO: restrictions and prefixing tables with smart_contract_caller
# TODO: Don't hard code this

# Note password is auto generated every time docker instance is built, password is hardcoded right now and must be changed to run
# Dockerfile regenerates random password on every build.
ENGINE = create_engine("mysql://seneca_test:JpJIzaoee2@127.0.0.1:3306/seneca_test")
CONN = ENGINE.connect()
METADATA.bind=ENGINE


# Alternate implementation, using sql directly, ultimately we probably want this done by an outside process.
# Dockerfile regenerates random password on every build.
db = MySQLdb.connect(host="127.0.0.1",    # your host, usually localhost
                     user="seneca_test",         # your username
                     passwd="JpJIzaoee2",  # your password
                     db="seneca_test")        # name of the data base
cur = db.cursor()

# http://docs.sqlalchemy.org/en/latest/core/tutorial.html


def outside_table(sc_addr, name):
    """
    Always read-only. To edit another smart_contract's tables, you must use the methods that contract exports

    """
    pass

def run_batch(ops):
    """
    """
    # TODO: This should be implemnted more efficiently than just running each command individually.
    for o in ops:
        o.run()


def tup_defaults(t, prototype):
    return tuple(map(lambda x_y: x_y[0] if x_y[0] else x_y[1], zip_longest(t, prototype)))


class StrLimitLen(object):
    def __init__(self, l):
        self.length_limit = l

def str_len(l):
    return StrLimitLen(l)

class QueryConstraint(object):
    def __init__(self, table_name, qc_type, column_name, value):
#        print("***QueryConstraint***")
#        print(table_name, qc_type, column_name, value)
        self.qc_type = qc_type
        self.column_name = column_name
        self.value = value
        self.table_name = table_name

    # TODO: this should go to a serialized intermediate representation, go through access control, then converted to SQL
    def to_sql(self):
        qc_to_sql = {
            # TODO: should probably add backticks to column names
            'equals': lambda x,y: '%s.%s = %s' % (self.table_name, str(x), str(y)),
            'less_than': lambda x,y: '%s.%s < %s' % (self.table_name, str(x), str(y)),
            'greater_than': lambda x,y: '%s.%s > %s' % (self.table_name, str(x), str(y)),
        }

        assert self.qc_type in qc_to_sql, "Failed to idendtify query constraint type."

        return qc_to_sql[self.qc_type](self.column_name, self.value)


class QueryLimit(object):
    def __init__(self, quantity):
        self.quantity = quantity

    def to_sql(self):
        return " LIMIT %d" % self.quantity


class QuerySort(object):
    # TODO: decide whether users are allowed to order by multiple columns, if so modify
    def __init__(self, table_name, column_name, desc):
        self.column_name = column_name
        self.desc = desc
        self.table_name = table_name

    def to_sql(self):
        desc = 'DESC' if self.desc else ''
        return " ORDER BY %s.%s %s" % (self.table_name, self.column_name, desc)



# TODO: for batching, run needs to be broken into 2 steps, create query and execute.

class ConstrainableQuery(object):
    # TODO: sanitize input on everything
    def __init__(self, t_table):
        self.t_table = t_table
        self.modifiers = []

    def append_constraint(self, *args):
        print("appending constraint", self.t_table.name)
        print(*args)
        self.modifiers.append(QueryConstraint(self.t_table.name, *args))
        return self

    def where_equals(self, column_name, val):
        return self.append_constraint('equals', column_name, val)

    def where_lt(self, column_name, val):
        return self.append_constraint('less_than', column_name, val)

    def where_gt(self, column_name, val):
        return self.append_constraint('greater_than', column_name, val)

    #Todo: figure out all features we want? Like? Regex? What else?

    def get_constraints(self):
        return map(lambda x: x.to_sql(),
            filter(lambda x: type(x) == QueryConstraint, self.modifiers)
        )


    def build_where_query_fragment(self):
        where_sql = ' AND '.join(self.get_constraints())

        if where_sql:
            where_sql = 'WHERE %s' % where_sql

        return where_sql


class JoinPartialQuery(ConstrainableQuery):

    def __init__(self, main_query, t_table, on_src=None, on_dest=None, alias=None, j_type='left_outer'):
        assert on_src is not None
        assert on_dest is not None

        self.t_table = t_table
        self.primary_table_name = main_query.t_table.name
        self.main_query = main_query
        self.primary_table_on = on_src
        self.this_table_on = on_dest
        self.alias = alias
        self.j_type = j_type
        self.modifiers = []


#     def is_null(self, val=True):
# #         self.modifiers.append(QueryLimit(count))
# #         return self
#

    def build_query(self):
        return ' '.join([ self.main_query.build_query(),
                          self.build_join_on_query_fragment()
                   ])

    def build_query(self):
        return ' '.join([self.main_query.build_select(),
                         self.build_join_on_query_fragment(),
                         self.build_where_query_fragment(),
                         self.main_query.build_order(),
                         self.main_query.build_limit()])

    def build_join_on_query_fragment(self):
        if self.j_type == 'left_outer':
            return "LEFT JOIN %s ON %s.%s = %s.%s" % (
                self.t_table.name,
                self.primary_table_name,
                self.primary_table_on,
                self.t_table.name,
                self.this_table_on
            )


        else:
            raise NotImplementedError()


    def build_where_query_fragment(self):

        all_constraints = list(self.main_query.get_constraints()) + list(self.get_constraints())

        where_sql = ' AND '.join(all_constraints)

        if where_sql:
            where_sql = 'WHERE %s' % where_sql

        return where_sql

    def limit(self, val):
        self.main_query.limit(val)
        return self


    def order_by(self, column_name, desc=False):
        self.main_query.modifiers.append(QuerySort(self.t_table.name, column_name, desc))
        return self


    def run(self):
        sql_expr = self.build_query()

        cur.execute(sql_expr)

        numrows = cur.rowcount

        # Get and display one row at a time
        ret = []
        col_names = self.t_table.get_columns()

        for x in range(0, numrows):
            vals = cur.fetchone()
            #val_dict = dict(zip(col_names, vals))

            ret.append(vals)

        return ret






class DeleteQuery(ConstrainableQuery):
    # TODO: sanitize input on everything

    # TODO: further dedupe with SelectQuery and move to ConstrainableQuery
    def run(self):
        where_sql = self.build_where_query_fragment()

        sql_expr = ' '.join(['DELETE from %s' % self.t_table.name, where_sql])

        cur.execute(sql_expr)
        db.commit()

        numrows = cur.rowcount

        return {'deleted_row_count': numrows}


class SelectQuery(ConstrainableQuery):
    # TODO: sanitize input on everything
    # TODO: results should probably be returned as a list of (dict or named tuple)

    def limit(self, count):
        self.modifiers.append(QueryLimit(count))
        return self


    def order_by(self, column_name, desc=False):
        self.modifiers.append(QuerySort(column_name, desc))
        return self


    def easy_join(self, secondary_table, on_src=None, on_dest=None, alias=None):
        '''
        left outer join, ordered by on_src, results
        '''
        return JoinPartialQuery(self, secondary_table, on_src, on_dest, alias)


    def build_select(self):
        return 'SELECT * FROM %s' % self.t_table.name

    def build_limit(self):
        limit = list(filter(lambda x: type(x) == QueryLimit, self.modifiers))
        assert len(limit) <= 1, "Error, encountered multiple limit statements."
        return '' if not limit else limit[0].to_sql()

    def build_order(self):
        sort = list(filter(lambda x: type(x) == QuerySort, self.modifiers))
        assert len(sort) <= 1, "Error, encountered multiple order-by statements."
        return '' if not sort else sort[0].to_sql()

    def build_query(self):
        return ' '.join([self.build_select(),
                         self.build_where_query_fragment(),
                         self.build_order(),
                         self.build_limit()])

    # TODO: move this method to the base query class, require all child classes to implement build_query
    def __str__(self):
        return self.build_query()


    def run(self):
        sql_expr = self.build_query()

        cur.execute(sql_expr)

        numrows = cur.rowcount

        # Get and display one row at a time
        ret = []
        col_names = self.t_table.get_columns()

        for x in range(0, numrows):
            vals = cur.fetchone()
            val_dict = dict(zip(col_names, vals))

            ret.append(val_dict)

        return ret




# TODO: Validate assumption that this can probably never be secure as implemented
# TODO: This is a preview of an interface, it almost certainly must be implemented
# in something other than Python to be secure, or we'll have to substatially change
# how we eval and run smart contracts
class TTable(object):
    def __init__(self, sa_table):
        self.sa_table = sa_table
        self.call_stack = []
        self.name = sa_table.fullname

    def run(self):
        temp_ref = self.sa_table
        cs = self.call_stack
        self.call_stack = []

        if cs[0] == 'insert':
            CONN.execute(temp_ref.insert(), cs[1])
        else:
            raise NotImplementedError()


    def select(self):
        return SelectQuery(self)


    def get_columns(self):
        sa_cs = self.sa_table.columns
        #map(lambda x: x.split('.')[-1], sa_cs)
        return list(map(lambda x:x.key, sa_cs))


    def insert(self, dict_list):
        # TODO: move this to a separate class
        # TODO: Don't use SQLAlchemy
        # TODO: sanitize table names, a-z, underscores, no leading underscores.
        self.call_stack.extend(['insert', dict_list])
        return self


    def delete(self):
        return DeleteQuery(self)


# TODO: function decorator that adds caller data, makes sure it's populated and pre-applies it to name
# @safe_name_prefix
def table(t_name, column_tup_list):
    # TODO: convert from sqlalchemy, make serializable
    """
    Create or retrieve table (always prepended with caller smart contract address).
    examples:

    u = st.table('users', [
        ('first_name', str_len(30)),
        ('last_name', str_len(30)),
        ('nick_name', str_len(30), True),
        ('balance', int)
    ])
    # Will always prepend table name with smart contract ID
    # outside_table(sc_addr, name)

    u.update(???).where(???).values(????).run()
    u.insert(????).run()
    u.insert(????).run()
    x = u.select(????).whatever().whatever().run()

    st.run(u.select([u.c.id])
           .where(users.c.id == )

    """
    # TODO: make sure metadata is safely handled and isn't leaking anywhere it shouldn't
    # TODO: Thinking name prefix safety is only for inserts, and drops, confirm.
    # TODO: safely apply whitelist to name, only allow a-z,0-9,_,-  and any mysql rules on names
    # TODO: see if we can restrict users from accessing closure scope on return functions, if we cannot, this must be implemented differently,
    # ultimately we may have to reimplment all this in our own interpreter.

    sc_id = seneca_internal.smart_contract_caller

    assert sc_id is not None, \
      "Something went wrong. This module should only every be called by smart contracts, the caller cannot be identified"

    safe_name = "%s_%s" % (seneca_internal.smart_contract_caller, t_name)
    t_name = None # Unsetting t_name so it cannot accidentally be used
    # Replace this and above logic with decorator function would be better

    def convert_to_sa_type(x):
        if x is int:
            return Integer
        elif type(x) == StrLimitLen:
            return String(x.length_limit)
        else:
            raise ValueError("Unsupported column type.")


    def create_column(c_tup):
        c_name, c_type, unique_con = tup_defaults(c_tup, (None, None, False))
        return Column(c_name, convert_to_sa_type(c_type), unique=unique_con)

    table = Table(safe_name, METADATA ,
       Column('id', Integer, Sequence('user_id_seq'), primary_key=True),
       *map(create_column, column_tup_list),
       # TODO: decide if we actually want autoload enabled
#       autoload_with=ENGINE,
#       check_exists=True,
#       autoload=True
    )

    # TODO: figure out what happens if the table already exists and make changes as needed
#    table.create(ENGINE)
    MetaData.create_all(METADATA, checkfirst=True)

    return TTable(table)


exports = {
    'outside_table': outside_table,
    'run_batch': run_batch,
    'str_len': str_len,
    'table': table,
}
