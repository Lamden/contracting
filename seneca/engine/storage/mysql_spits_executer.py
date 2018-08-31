'''
TODO: complex stuff, soft delete a permanent, create temporary, delete temporary
TODO: forbid queries with names matching temp tables

TODO: Currently circumventing main code block that selects special query actions
'''
import re
import copy
import MySQLdb
from seneca.engine.util import *

import seneca.engine.storage.mysql_executer as ex_base
from seneca.engine.storage.mysql_intermediate import *

unalterted_queries = [ DeleteRows,
                       UpdateRows,
                       InsertRows,
                       SelectRows,
                       CountUniqueRows,
                       CountRows,
                       DescribeTable,
]

dissallowed_queries = [ AddTableColumn,
                        DropTableColumn,
]

def make_temp_name(table_name):
    '''
    >>> make_temp_name('test')
    '$temp$test'
    '''
    return '$temp$' + table_name


def make_query_with_temp_name(q):
    '''
    >>> q = mysqli.InsertRows('test_users', ['username', 'first_name', 'balance'],
    ...   [['tester', 'test', 500],
    ...    ['tester2', 'two', 200],
    ...   ])
    >>> q1 = make_query_with_temp_name(q)
    >>> q1.table_name
    '$temp$test_users'
    '''
    q1 = copy.copy(q)
    q1.table_name = make_temp_name(q1.table_name)
    return q1


def CreateTableAction(ex, q):
    '''
    Clear state:
    >>> _ = ex.rollback()
    >>> _ = ex.cur.execute('DROP DATABASE seneca_test;')
    >>> _ = ex.cur.execute('CREATE DATABASE seneca_test;')
    >>> _ = ex.cur.execute('use seneca_test;')

    >>> _ = CreateTableAction(ex, ct)

    Confirm that table name is stored in temp_tables field, used for rollback and commit
    >>> ex.temp_tables
    {'test_users'}

    Confirm that the table is created (not established in this step if it's actually a temp table)
    >>> ex.cur.execute('SELECT * from seneca_test.$temp$test_users')
    0
    >>> print(ex.cur.fetchall())
    ()

    Confirm that the table is temporary (temporary tables are not returned by mysql's show tables)
    >>> ex.cur.execute('SHOW TABLES;')
    0

    Make sure no table has actually been created and commited.
    >>> ist = easy_db.Table.from_existing('INFORMATION_SCHEMA.TABLES').run(ex)
    >>> len(ist.select('table_name').where(ist.TABLE_NAME == 'test_users').run(ex))
    0
    >>> ex.rollback()

    Repeat process but commit:
    >>> _ = CreateTableAction(ex, ct)
    >>> _ = ex.commit()
    >>> ist = easy_db.Table.from_existing('INFORMATION_SCHEMA.TABLES').run(ex)
    >>> len(ist.select('table_name').where(ist.TABLE_NAME == 'test_users').run(ex))
    1
    >>> ex.temp_tables
    set()

    TODO: More unit tests on this.

    Dimensions of scenarios
    * (P)ermanent table exists [True, False]
    * (S)oft delete flag exists [True, False]
    * (T)empoary table exists [True, False]
    * (I)f_not_exists set on query [True, False]

    * P=True, S=False, T=True, I=any -> Exception (two version of table temp and per logically exist, this should never happen)
    * P=False, S=True, T=any, I=any -> Exception (soft delete but no permanent table to be soft deleted, this should never happen)
    * P=True, S=True, T=False, I=any -> run query not as temp query to create table
    ----

    * P=S, T=True, I=True -> run query as temp verify it works correctly with I on a temp table
    * P=S, T=False, I=any -> run a temporary query, create the temp table
    '''

    name = q.table_name
    temp_table_exists = name in ex.temp_tables
    permanent_table_exists = 0 < ex.cur.execute("SELECT table_name FROM INFORMATION_SCHEMA.TABLES where table_name = '{}'".format(name))
    soft_delete_exists = name in ex.soft_deleted_tables
    #q.if_not_exists

    q_type = type(q)
    assert q_type == CreateTable, 'Argument 1 q is wrong type, should be CreateTable got %' % str(q_type)

    if permanent_table_exists and (not soft_delete_exists) and temp_table_exists:
        Exception("SPITS is in an inconsitent state, temp table and permanent table exists, but no soft delete record is present!!!")

    if (not permanent_table_exists) and soft_delete_exists:
        Exception("SPITS is in an inconsitent state, soft delete record present but permanent table missing!!!")

    if permanent_table_exists and (not soft_delete_exists):
        if q.if_not_exists:
            return ex_base.SQLExecutionResult(True, "Permanent table already exists, but okay, if_not_exists is set to True")
        else:
            Exception("SPITS error, permanent table already exists.")
    else:
        # Important, temp tables are stored in executer temp table without temp table prefix
        ex.temp_tables.add(name)
        # Prefix added here for create query
        sql_str = make_query_with_temp_name(q).to_sql()

        # NOTE: A little janky
        sql_preamble_re = re.compile('^CREATE TABLE')
        assert re.match(sql_preamble_re, sql_str)
        new_query = re.sub(sql_preamble_re, 'CREATE TEMPORARY TABLE', sql_str)
        res = ex.cur.execute(new_query)

        return ex_base.format_result(q_type, ex.cur)


def ListTablesAction(ex, q):
    '''
    '''
#
#    TODO: finish this tests
#    Result comes from db:
#    >> _ = ex.commit()
#    >> str(ListTablesAction(ex,ListTables()))
#    "SQLExecutionResult({'success': True, 'data': ['test_users']})"
#
#    Soft delete table hidden:
#    >> _ = CreateTableAction(ex, ct)
#    >> _ = ex.commit()
#
#    '''
    q_type = type(q)
    ex.cur.execute(q.to_sql())

    sql_ex_res = ex_base.format_result(q_type, ex.cur)
    table_names = sql_ex_res.data

    table_names_temp = list(
                         set( ex.temp_tables | \
                              {t for t in table_names if t not in ex.soft_deleted_tables}
                         )
                       )
    sql_ex_res.data = table_names_temp

    # Not formatting
    return ex_base.SQLExecutionResult(True, sql_ex_res.data)


def DropTableAction(ex, q):
    '''
    Clear state:
    >>> _ = ex.rollback()
    >>> _ = ex.cur.execute('DROP DATABASE seneca_test;')
    >>> _ = ex.cur.execute('CREATE DATABASE seneca_test;')
    >>> _ = ex.cur.execute('use seneca_test;')

    Delete an uncommited table (temporary):
    >>> _ = CreateTableAction(ex, ct)
    >>> ex.temp_tables
    {'test_users'}

    >>> str(DropTableAction(ex, DropTable('test_users')))
    "SQLExecutionResult({'success': True, 'data': 'Uncommitted table test_users has been deleted.'})"

    >>> ex.temp_tables
    set()


    Clear state:
    >>> _ = ex.rollback()
    >>> _ = ex.cur.execute('DROP DATABASE seneca_test;')
    >>> _ = ex.cur.execute('CREATE DATABASE seneca_test;')
    >>> _ = ex.cur.execute('use seneca_test;')

    Soft delete a table and confirm name has been added to the soft_delete list:
    >>> _ = CreateTableAction(ex, ct)
    >>> _ = ex.commit()
    >>> str(DropTableAction(ex, DropTable('test_users')))
    "SQLExecutionResult({'success': True, 'data': 'Table test_users has been soft-deleted.'})"
    >>> ex.soft_deleted_tables
    {'test_users'}
    >>> ex.temp_tables
    set()

    >>> _ = ex.commit()

    Test that soft-deleting an already soft deleted table sends a failure:
    >>> str(DropTableAction(ex, DropTable('test_users')))
    'SQLExecutionResult({\\'success\\': False, \\'data\\': "SPITS ERROR: Attempting to delete a table that doesn\\'t logically exist"})'
    '''
    q_type = type(q)

    name = q.table_name
    temp_name = make_temp_name(name)

    temp_table_exists = name in ex.temp_tables
    permanent_table_exists = 0 < ex.cur.execute("SELECT table_name FROM INFORMATION_SCHEMA.TABLES where table_name ='{}'".format(name))
    soft_delete_exists = name in ex.soft_deleted_tables

    if temp_table_exists:
        # TODO: Make sure this is the right logic and in the right place
        assert permanent_table_exists == soft_delete_exists, "SPITS ERROR: Table delete status in inconsistent state."

        ex.cur.execute("DROP TEMPORARY TABLE %s" % temp_name)
        # TODO: validate result
        ex.temp_tables.remove(name)
        return ex_base.SQLExecutionResult(True, "Uncommitted table %s has been deleted." % name)

    elif permanent_table_exists and (not soft_delete_exists):
        ex.soft_deleted_tables.add(name)
        return ex_base.SQLExecutionResult(True, "Table %s has been soft-deleted." % name)

    else:
        return ex_base.SQLExecutionResult(False, 'SPITS ERROR: Attempting to delete a table that doesn\'t logically exist')



special_action_query_dict = { CreateTable: CreateTableAction,
                              ListTables: ListTablesAction,
                              DropTable: DropTableAction,
}

special_action_queries = list(special_action_query_dict.keys())

# TODO: Dedupe with main executer
class Executer(object):
    def __init__(self, username, password, db, host, port=3306):
        ''' Tested below '''
        self.conn = MySQLdb.connect(host=host, user=username, passwd=password,
                                    db=db, port=port)
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        self.temp_tables = set()
        self.soft_deleted_tables = set()

    def __call__(self, query):
        q_type = type(query)
        assert issubclass(q_type, Query), 'The passed parameter is not a query.'

        try:
            if q_type in unalterted_queries:

                if (query.table_name in self.soft_deleted_tables
                    and query.table_name not in self.temp_tables):
                    raise Exception("Table does not exist, (soft deleted).")

                if query.table_name in self.temp_tables:
                    query = make_query_with_temp_name(query)

                self.cur.execute(query.to_sql())
                return ex_base.format_result(q_type, self.cur)

            elif q_type in dissallowed_queries:
                raise Exception('Dissallowed query. Incompatible with SPITS.')

            elif q_type in special_action_queries:
                return special_action_query_dict[q_type](self, query)

            else:
                raise Exception("Unrecognized query type. \
SPITS does not have the needed info to execute this query.")

        except Exception as err:
            # Note: This function may return a formated result, or it may reraise the error
            return ex_base.handle_error(q_type, err)

    def _clear(self):
        self.temp_tables = set()
        self.soft_deleted_tables = set()


    def commit(self):
        ''' Tested elsewhere '''
        # DML commit
        self.conn.commit()

        # DDL pseudo-commit
        for t in self.temp_tables:
            name = t
            temp_name = make_temp_name(name)

            q_str = 'CREATE TABLE {name} LIKE {temp_name};\
                     INSERT {name} SELECT * FROM {temp_name};\
                     DROP TEMPORARY TABLE {temp_name};'.format(**locals())

            self.cur.execute(q_str)

        for t in self.soft_deleted_tables:
            self.cur.execute("DROP TABLE %s;" % t)

        # Purge internal scratch
        self._clear()


    def rollback(self):
        ''' Tested elsewhere '''
        # DML rollback
        self.conn.rollback()

        # DDL pseudo-rollback
        for t in self.temp_tables:
            self.cur.execute("DROP TEMPORARY TABLE %s;" % make_temp_name(t))

        # Purge internal scratch
        self._clear()

    def many(self, queries):
        # TODO: Test the speed on this
        # TODO: Error handling
        # TODO: Test atomicity
        for q in queries:
            self.cur.execute(q.to_sql())
        self.conn.commit()

        return ex_base.SQLExecutionResult(True, None)

    def kill(self):
        self.cur.close()
        self.conn.close()



def run_tests(deps_provider):
    '''
    Setup/clear state:
    >>> _ = spex.rollback(); spex.soft_deleted_tables |  spex.temp_tables
    set()
    >>> _ = spex.cur.execute('DROP DATABASE IF EXISTS seneca_test;')
    >>> _ = spex.cur.execute('CREATE DATABASE seneca_test;')
    >>> _ = spex.cur.execute('use seneca_test;')

    List empty:
    >>> str(ListTablesAction(spex,ListTables()))
    "SQLExecutionResult({'success': True, 'data': []})"

    Create temporary table:
    >>> _ = CreateTableAction(spex, ct)
    >>> spex.temp_tables
    {'test_users'}

    List with results from temporary table record in executer:
    >>> str(ListTablesAction(spex,ListTables()))
    "SQLExecutionResult({'success': True, 'data': ['test_users']})"

    List with results from permanent table:
    >>> spex.commit()
    >>> spex.temp_tables
    set()
    >>> str(ListTablesAction(spex,ListTables()))
    "SQLExecutionResult({'success': True, 'data': ['test_users']})"

    Results exclude soft deleted table:
    >>> str(DropTableAction(spex, DropTable('test_users')))
    "SQLExecutionResult({'success': True, 'data': 'Table test_users has been soft-deleted.'})"

    Verify soft delete of commited table:
    >>> spex.soft_deleted_tables
    {'test_users'}
    >>> str(ListTablesAction(spex,ListTables()))
    "SQLExecutionResult({'success': True, 'data': []})"

    Create and delete with commited table that's soft deleted:
    >>> _ = CreateTableAction(spex, ct)
    >>> spex.temp_tables
    {'test_users'}
    >>> spex.soft_deleted_tables
    {'test_users'}

    >>> ist = easy_db.Table.from_existing('INFORMATION_SCHEMA.TABLES').run(spex)

    Confirm permanent table still exists
    >>> len(ist.select('table_name').where(ist.TABLE_NAME == 'test_users').run(spex))
    1

    #### Confirm temporary table exists ####
    >>> tmp = easy_db.Table.from_existing(make_temp_name(ct.table_name)).run(spex)
    >>> tmp.count().run(spex)
    0

    >>> _ = spex.rollback()

    Confirm permanent table still exists
    >>> len(ist.select('table_name').where(ist.TABLE_NAME == 'test_users').run(spex))
    1
    >>> spex.temp_tables
    set()
    >>> spex.soft_deleted_tables
    set()

    Confirm temporary table gone
    >>> try:
    ...     tmp = easy_db.Table.from_existing(make_temp_name(ct.table_name)).run(bex)
    ... except Exception as e:
    ...     print(e)
    {'error_code': 1146, 'error_message': "Table 'seneca_test.$temp$test_users' doesn't exist"}


    #### TEST: Write to temporary table ####
    Setup/clear state:
    >>> _ = spex.rollback(); spex.soft_deleted_tables |  spex.temp_tables
    set()
    >>> _ = spex.cur.execute('DROP DATABASE IF EXISTS seneca_test;')
    >>> _ = spex.cur.execute('CREATE DATABASE seneca_test;')
    >>> _ = spex.cur.execute('use seneca_test;')

    Create temporary table:
    >>> _ = CreateTableAction(spex, ct)
    >>> spex.temp_tables
    {'test_users'}
    >>> tmp = easy_db.Table.from_existing(ct.table_name).run(spex)
    >>> tmp.count().run(spex)
    0
    >>> tmp.insert([{'username':'test_perm'}]).run(spex)
    {'last_row_id': 1, 'row_count': 1}
    >>> tmp.count().run(spex)
    1

    >>> tmp_with_tmp_name = easy_db.Table.from_existing(make_temp_name(ct.table_name)).run(bex)
    >>> tmp_with_tmp_name.count().run(bex)
    1
    >>> _ = spex.commit()

    >>> tmp.count().run(bex)
    1
    >>> tmp.count().run(spex)
    1

    '''
    import doctest, sys
    import seneca.engine.storage.mysql_intermediate as mysqli
    import seneca.engine.storage.easy_db as easy_db
    from typing import Tuple

    from seneca.engine.storage.mysql_executer import Executer as Raw_Executer
    spex,bex = deps_provider(Tuple[Executer, Raw_Executer])
    ex = spex


    ct = CreateTable(
          'test_users',
          AutoIncrementColumn('id'),
          [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
            ColumnDefinition('drivers_licence_unmber', SQLType('VARCHAR', 30), True),
            ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
            ColumnDefinition('balance', SQLType('BIGINT'), False),
    ])

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
