'''
# Simple tabular datastore #
* Uses myrocks to support SQL operations on rocksdb
* Right now relying on yet to be built execution environment to force squential evaluation of contracts
  * Not doing any concurrency control/transactions. Consistency maintained by that sequential evaluation

* Must start work on Seneca import system so we can inject caller address here.
  * Must not be a singleton like standard Python imports because it's very possible this lib will be called by multiple smart contracts in chain and need to give each its own instance
  * Alternatively, it could just always pass smart_contract_id as first arg
  * Caller could just be injected as module-global var

* Need a way tie all mutations smart contract address of caller
  * Probably do not want this for data access

* Maybe provide a transaction interface for performance (or if some kind of parallel execution is eventually allowed.)
* Note: currently no foreign keys allowed in Myrocks, this is a feature under development so we may want to add it when they do.

* Big TODOs:
  * Make this secure.
    * Serialized requests to a separate process
      * Validate before running based on caller.
      * Issue session like webserver, make sure a smart contract can't hijack a session of another one running.
    * Input sanitization
  * Decide: do we allow joins across smart contracts?
    * Peformance implications for sure.
    * It will limit future architecture possibilities
  * Run batch
  * Version one feature list. LIKE? Regex match?

  * Outside table foreign table, something
  * Warning for queries created and never run. Though the syntax is consistent, and a finalizer like run() is necessary
  for queries created by chained methods, else how would we know to runs a .select() when it's unknown if the author will
  be adding a .where_equals() or running as is.
    * Plugin to traverse the AST, count up queries, then count up run() invocations and warn if they don't add up.

  * User types to designate safe and unsafe names (tables, columns, etc)
  * Make sure we're using cursor correctly

TODO:
  * Table alteration methods
    * Decide whether or not they should be methods or module functions
    * drop table, add column, drop column
    * decide what invocation should look like ".run()"? run_<some_name> (no 'run')
  * get_table method that populates table object with data from table in db
'''

# TODO: make names of conversion functions uniform so it's easy to see where they are and add new types
# TODO: configurable verbosity
# TODO: verify this is being called each time it's imported.

from itertools import zip_longest
import warnings
import MySQLdb
import datetime

# TODO: Replace this with the real engine from Cilantro

# Dockerfile regenerates random password on every build.
TEMP_PASSWORD='H9ECjzW03N'

conn = MySQLdb.connect(host="127.0.0.1",    # your host, usually localhost
                     user="seneca_test",         # your username
                     passwd=TEMP_PASSWORD,  # your password
                     db="seneca_test")        # name of the data base
cur = conn.cursor()


def outside_table(sc_addr, name):
    """
    Always read-only. To edit another smart_contract's tables, you must use the methods that contract exports
    """
    pass


def run_batch(ops):
    # TODO: This should be implemnted more efficiently than just running each command individually.
    for o in ops:
        o.run()


def _run_read(q):
    cur.execute(q)
    return cur


def _run_write(q):
    cur.execute(q)
    conn.commit()
    return cur


def _run_writes(qs):
    for q in qs:
        cur.execute(q)
    conn.commit()
    return cur


def surround(s, x):
    return s + x + s


def in_quotes(x):
    return surround('\'', x)


def in_backticks(x):
    return surround('`', x)


class StrLimitLen(object):
    """A simple object that is passed as a type in column definitions, it
    represents a string with a fixed length
    """
    def __init__(self, l):
        self.length_limit = l


def str_len(l):
    """Utility function so StrLimitLen is invoked in lower case to look more
    like 'int' and other built in types.
    """
    return StrLimitLen(l)

def sql_escapes(s):
    # TODO: make sure everything I need is here.
    import re
    return re.sub("'", "''", s)



def sql_str(x):
    """ Casting python types to valid strings for sql values, currently used to
    quote strings.
    """
    t = type(x)
    if t == str:
        return "'%s'" % sql_escapes(x)
    elif t == datetime.datetime:
        # TODO: figure out local time
        return "'%s'" % x
    elif x is None:
        return 'NULL'
    else:
        return str(x)


class QueryConstraint(object):
    """Represents the contents of an SQL where clause, '=', '>', '<', and (maybe
    other stuff eventually).
    """
    def __init__(self, table_name, qc_type, column_name, value):
        self.qc_type = qc_type
        self.column_name = safe_column_name(column_name)
        self.value = value
        self.table_name = table_name

    # TODO: this should go to a serialized intermediate representation, go through access control, then converted to SQL
    def to_sql(self):
        qc_to_sql = {
            # TODO: should probably add backticks to column names
            'equals': lambda x,y: '%s.%s = %s' % (self.table_name, str(x), sql_str(y)),
            'less_than': lambda x,y: '%s.%s < %s' % (self.table_name, str(x), str(y)),
            'greater_than': lambda x,y: '%s.%s > %s' % (self.table_name, str(x), str(y)),
            'all_rows': lambda x,y: 'TRUE',
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
        self.column_name = safe_column_name(column_name)
        self.desc = desc
        self.table_name = table_name

    def to_sql(self):
        desc = 'DESC' if self.desc else ''
        return " ORDER BY %s.%s %s" % (self.table_name, self.column_name, desc)


def require_constraint_on_run(f):
    '''Function decorator: useful for query methods, which would be bad to run
    accidentally when applied to all rows, i.e. updates and deletes'''
    def ret(obj):
        assert list(obj.get_constraints()), "To prevent unintended modification to all rows, \
        destructive opperations must always contain a constraint, either 'where_*(...)', or to modify \
        all rows, use .update(...).all_rows()"

        return f(obj)

    return ret


class ConstrainableQuery(object):
    # TODO: sanitize input on everything
    def __init__(self, table):
        self.table = table
        self.modifiers = []

    def append_constraint(self, *args):
        self.modifiers.append(QueryConstraint(self.table.name, *args))
        return self

    # TODO: create safe_val function and apply to all vals below
    def where_equals(self, column_name, val):
        return self.append_constraint('equals', safe_column_name(column_name), val)

    def where_lt(self, column_name, val):
        return self.append_constraint('less_than', safe_column_name(column_name), val)

    def where_gt(self, column_name, val):
        return self.append_constraint('greater_than', safe_column_name(column_name), val)

    def all_rows(self):
        return self.append_constraint('all_rows', None, None)

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


class UpdateQuery(ConstrainableQuery):
    def __init__(self, table, set_column_value):
        self.set_column_value = safe_column_name(set_column_value)
        self.table = table
        self.modifiers = []

    # Inherits where-methods from ConstrainableQuery

    def build_query(self):
        set_clauses = ', '.join(['%s=%s' % (k,sql_str(v)) for k,v in self.set_column_value.items()])

        return ' '.join([
            'UPDATE %s' % self.table.name,
            'SET %s' % set_clauses,
            self.build_where_query_fragment()
        ])

    @require_constraint_on_run
    def run(self):
        # There must be where constraints
        assert list(self.get_constraints()), "To prevent unintended updates to all rows, \
        updates must always contain a conatraint, either 'where_*(...)', or to update \
        all rows, use .update(...).all_rows()"

        sql_expr = self.build_query()

        cur.execute(sql_expr)
        conn.commit()

        numrows = cur.rowcount

        return {'updated_rows_count': numrows}




        '''
    # TODO: move this method to the base query class, require all child classes to implement build_query
    def __str__(self):
        return self.build_query()


    def run(self):
        sql_expr = self.build_query()

        cur.execute(sql_expr)
        #?? conn.commit()

        numrows = cur.rowcount

        # Get and display one row at a time
        ret = []
        col_names = self.table.get_columns()

        for x in range(0, numrows):
            vals = cur.fetchone()
            val_dict = dict(zip(col_names, vals))

            ret.append(val_dict)

        return ret

        '''



class JoinPartialQuery(ConstrainableQuery):

    def __init__(self, main_query, table, on_src=None, on_dest=None, alias=None, j_type='left_outer'):
        assert on_src is not None
        assert on_dest is not None

        self.table = table
        self.primary_table_name = main_query.table.name
        self.main_query = main_query
        self.primary_table_on = on_src
        self.this_table_on = on_dest
        self.alias = alias
        self.j_type = j_type
        self.modifiers = []


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
                self.table.name,
                self.primary_table_name,
                self.primary_table_on,
                self.table.name,
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
        self.main_query.modifiers.append(QuerySort(self.table.name, safe_column_name(column_name), desc))
        return self


    def run(self):
        sql_expr = self.build_query()

        cur.execute(sql_expr)
        numrows = cur.rowcount

        # Get and display one row at a time
        ret = []
        col_names = self.table.column_names

        # TODO: Don't conflate table column list from query columns, only the same if it's 'select *'
        # Currently 'select *' is all that's supported, but that could change.
        self.table.column_names
        self.main_query.table.column_names

        for x in range(0, numrows):
            vals = cur.fetchone()

            assert len(vals) == len(self.main_query.table.column_names) + \
              len(self.table.column_names), 'Malformed data received from MyRocks server.'

            # Main table results
            # TODO: make sure the correct types are being returned.
            r = dict(zip(self.main_query.table.column_names, vals))

            # Joined results
            # TODO: make sure column names with leading underscores are disallowed
            r['_joined'] = {self.table.name: dict(zip(self.table.column_names, vals[(-(len(self.table.column_names))):]))}

            ret.append(r)

        return ret


class DeleteQuery(ConstrainableQuery):
    # TODO: sanitize input on everything
    # TODO: further dedupe with SelectQuery and move to ConstrainableQuery
    @require_constraint_on_run
    def run(self):
        where_sql = self.build_where_query_fragment()

        sql_expr = ' '.join(['DELETE from %s' % self.table.name, where_sql])

        cur.execute(sql_expr)
        conn.commit()

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
        return 'SELECT * FROM %s' % self.table.name


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
        col_names = self.table.column_names

        for x in range(0, numrows):
            # TODO: casting function from SQL data to Python types goes here.
            vals = cur.fetchone()
            val_dict = dict(zip(col_names, vals))

            ret.append(val_dict)

        return ret


class InsertQuery(object):
    def __init__(self, ttable, rows_list_of_dicts):
        self.row_data = rows_list_of_dicts
        self.table = ttable


    def get_row_keys(self):
        return list(map(lambda x: list(x.keys()), self.row_data))


    def validate_row_data(self):
        keys_list = self.get_row_keys()
        assert len(keys_list) > 0, 'Error: No keys found for insert.'
        assert all(x == keys_list[0] for x in keys_list), 'Error: when \
        inserting multiple records at once, all dicts must have keys much match'

        # TODO: should probably validate against known table columns here


    def build_query(self):
        self.validate_row_data()

        keys = self.get_row_keys()[0]

        values_list = list(map(lambda row: [row[k] for k in keys],
          self.row_data))


        def render_row_data(r):
            r_str = map(sql_str, r)
            return '(%s)' % ', '.join(r_str)


        # TODO: if columns are formatted like this elsewhere, abstract this logic
        columns_str = '(%s)' % ', '.join(map(lambda x: '`%s`' % x, keys))
        all_values_str = ', '.join(map(render_row_data, values_list))

        return ' '.join([
          'INSERT INTO %s %s' % (self.table.name, columns_str),
          'VALUES %s' % all_values_str
        ])


    def run(self):
        sql_expr = self.build_query()

        count = cur.execute(sql_expr)
        conn.commit()
        last_row = cur.lastrowid

        return {'inserted_rows_count': count, 'last_row_inserted_id': last_row}



# TODO: enforce a unique delimiter that is dissalowed in user content to prevent strategic collisions, maybe dollar
# TODO: Validate assumption that this can probably never be secure as implemented
# TODO: This is a preview of an interface, it almost certainly must be implemented
# in something other than Python to be secure, or we'll have to substatially change
# how we eval and run smart contracts
def safe_table_name(name):
    # TODO: Refactor this library, split out the functionality used by smart contracts and internally
    if 'seneca_internal' in globals():
        return "%s$%s" % (seneca_internal.smart_contract_caller, name)
    else:
         return name


def safe_column_name(name):
    # TODO: apply whitelist
    return name


def safe_constraint_name(tbl_name, col_name):
    return '%s$%s' % (safe_table_name(tbl_name), safe_column_name(col_name))


def to_sql_type_str(x):
    # return values used when creating queries (that will be casting python data types to sql)
    if x is int:
        return 'BIGINT'
    elif type(x) == StrLimitLen:
        return 'VARCHAR(%d)' % x.length_limit
    # TODO: decide if this is a gotcha.
    elif x is str:
        return 'TEXT'
    elif x is datetime.datetime:
        return 'DATETIME'
    else:
        raise ValueError("Unsupported column type.")
    # TODO: decimal, date time


def join_non_empty(d, xs):
    return d.join(list(filter(lambda x:x, xs)))


def create_table(*args, **kwargs):
    """Table factory, currently just runs Table constructor, may add more stuff later."""
    return Table.generate_from_unsafe_name(*args, **kwargs)


def get_table(name):
    return Table.generate_from_db_table(name)


def make_unique_constraint_name(safe_table_name, raw_column_name):
    return 'seneca_unique$%s$%s' % (safe_table_name, raw_column_name)


def _just_drop_table(safe_name):
    q = 'DROP TABLE %s;' % safe_name
    _run_write(q)


def drop_table(unsafe_unknown_type_t):
    is_table = False

    if type(unsafe_unknown_type_t) == Table:
        unsafe_t_str = unsafe_unknown_type_t._unsafe_name_without_prefix
        is_table = True
    elif type(unsafe_unknown_type_t) == str:
        unsafe_t_str = unsafe_unknown_type_t
    else:
        raise TypeError("%s only exepts Tables and strings (table names)" % func.__name__)

    _just_drop_table(safe_table_name(unsafe_t_str))

    if is_table:
        del(unsafe_unknown_type_t)


def add_column(table, column_desc):
    # TODO: validate column name and table name
    column_name = column_desc[0]
    column_type = column_desc[1]
    column_is_unique = len(column_desc) == 3 and column_desc[2]

    qs = []

    qs.append(' '.join([ 'ALTER TABLE',
                            table.name,
                            'ADD COLUMN',
                            column_name,
                            to_sql_type_str(column_type),
                            'AFTER',
                            table.column_names[-1]
    ]))

    if column_is_unique:
        qs.append(' '.join([ 'ALTER TABLE',
                            table.name,
                            'ADD CONSTRAINT',
                            make_unique_constraint_name(table.name, column_name),
                            'UNIQUE (',
                            column_name,
                            ');'
        ]))

    _run_writes(qs)
    table.column_names.append(column_name)


def drop_column(table, column_name):
    # TODO: validate column name and table name
    drop_column_query = ' '.join([ 'ALTER TABLE',
                                    table.name,
                                    'DROP COLUMN',
                                    column_name,
                                    ';',
    ])
    res = _run_write(drop_column_query)

    # update table columns
    table.column_names = list(filter(lambda x: x != column_name, table.column_names))


class Table(object):
    """Represents a MyRocks table. Creating this object in a smart contract will
    automatically create the table as well.
    """

    def __init__(self, name, column_spec):
        self.name = name # VERY IMPORTANT
        self.column_spec = column_spec
        self._create(if_not_exists=True)

        self.column_names = ['id'] + [x[0] for x in column_spec]

    @classmethod
    def generate_from_unsafe_name(cls, name, column_spec):
        safe_name = safe_table_name(name)
        return cls(safe_name, column_spec)

    @classmethod
    def generate_from_db_table(cls, name):
        #Generate column spec

        #TODO: describe table
        #TODO: for each colum, get name, convert sql type to python type
        #TODO: probably should get unique constraint as well, but now not critical
        #TODO: build column spec
        raise NotImplementedError
        column_spec = '...'

        return generate_from_unsafe_name(cls, name, column_spec)


    def _create(self, if_not_exists=True):
        # TODO: sanitize column names

        id_column_str = 'id int AUTO_INCREMENT NOT NULL'
        column_spec_strs = list(map(
            lambda x:'%s %s' % (x[0], to_sql_type_str(x[1]))
            , self.column_spec
        ))


        def make_constraint(x):
            return 'CONSTRAINT %s UNIQUE (%s)' % (
              make_unique_constraint_name(self.name, x), x
            )

        unique_constraints = [ make_constraint(x[0]) for x in self.column_spec if len(x) == 3 and x[2]]

        # Everything inside perens needs commas
        #

        query = join_non_empty(' ',
          [ 'CREATE TABLE',
            'IF NOT EXISTS' if if_not_exists else '',
            self.name,
            '\n(',
            join_non_empty(',\n',
            [ id_column_str,
              *column_spec_strs,
              *unique_constraints,
              'PRIMARY KEY (id)',
            ]),
            '\n);',
        ])

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            ret = cur.execute(query)
            conn.commit()
            return ret


    def select(self):
        return SelectQuery(self)


    def update(self, set_column_value):
        return UpdateQuery(self, set_column_value)


    def insert(self, rows_list_of_dicts):
        return InsertQuery(self, rows_list_of_dicts)


    def delete(self):
        return DeleteQuery(self)


exports = {
    'outside_table': outside_table,
    'run_batch': run_batch,
    'str_len': str_len,
    'create_table': create_table,
    'drop_table': drop_table,
    'add_column': add_column,
    'drop_column': drop_column,
    'get_table': get_table
}
