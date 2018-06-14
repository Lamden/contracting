'''
'''

import re
from seneca.seneca_internal.util import *

import seneca.seneca_internal.storage.mysql_executer as ex_base
from seneca.seneca_internal.storage.mysql_intermediate import *

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

def CreateTableAction(ex, q):
    # TODO: see if table exists
    ex.temp_tables.append(q.table_name)

    sql_str = q.to_sql()

    # NOTE: A little janky
    sql_preamble_re = re.compile('^CREATE TABLE')
    # TODO: if assertion fails, return bad SQLExecutionResult.
    assert re.match(sql_preamble_re, sql_str)

    new_query = re.sub(sql_preamble_re, 'CREATE TEMPORARY TABLE', sql_str)
    res = ex.cur.execute(new_query)

    return ex_base.format_result(res, ex.cur)


def ListTablesAction(ex, q):
    sql_ex_res = ex_base.format_result(ex.cur.execute(q.to_sql()))
    table_names = sql_ex_res.data

    table_names_temp = list(
                         set( ex.temp_tables + \
                              [t for t in table_names if not in ex.soft_deleted_tables]
                         )
                       )
    sql_ex_res.data = table_names_temp
    return sql_ex_res.data


def DropTableAction(ex, q):
    # TODO: see if table exists
    ex.soft_deleted_tables.append(q.table_name)
    return SQLExecutionResult(True, "Table %s has been soft-deleted." % q.table_name)


special_action_query_dict = { CreateTable: CreateTableAction,
                              ListTables: ListTablesAction,
                              DropTable: DropTableAction,
}

special_action_queries = list(special_action_query_dict.keys())

class Executer(object):
    def __init__(self, username, password, db, host, port=3306):
        self.conn = MySQLdb.connect(host=host, user=username, passwd=password,
                                    db=db, port=port)
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        self.temp_tables = []
        self.soft_deleted_tables = []

    @classmethod
    def init_local_noauth_dev(cls, db_name='seneca_test'):
        s = cls('root', '', '', 'localhost')
        s.cur.execute('CREATE DATABASE IF NOT EXISTS {};'.format(db_name))
        s.cur.execute('use {};'.format(db_name))
        s.conn.database = db_name

        return s

    def __call__(self, query):
        q_type = type(query)
        assert issubclass(q_type, Query), 'The passed parameter is not a query.'

        try:
            if q_type in unalterted_queries:
                if query.table_table in self.soft_deleted_tables:
                    raise Exception("Table does not exist, (soft deleted).")

                self.cur.execute(query.to_sql())
                return ex_base.format_result(q_type, self.cur)

            elif q_type in dissallowed_queries:
                raise Exception('Dissallowed query. Incompatible with SPITS.')

            elif q_type in special_action_queries:
                return special_action_query_dict(q_type)(self, query):

            else:
                raise Exception("Unrecognized query type. SPITS does not have the needed info to execute this query."

        except Exception as err:
            # Note: This function may return a formated result, or it may reraise the error
            return handle_error(q_type, err)

    def commit(self):
        for t in self.temp_tables:
            # TODO: Copy any temp tables to perm tables
            # TODO: Drop temp tables
            pass
        for t in self.soft_deleted_tables:
            # TODO: Delete any soft deleted tables
            pass

        self.temp_tables = []
        self.soft_deleted_tables = []

        self.conn.commit()


    def rollback(self):
        for t in self.temp_tables:
            # TODO: Drop temp tables
            pass
        self.temp_tables = []
        self.soft_deleted_tables = []

        self.conn.rollback()


    def many(self, queries):
        # TODO: Test the speed on this
        # TODO: Error handling
        # TODO: Test atomicity
        for q in queries:
            self.cur.execute(q.to_sql())
        self.conn.commit()

        return SQLExecutionResult(True, None)
