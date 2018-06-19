'''
MySQL query execution and results parsing

TODOs:
  * Replace asserts with custom exceptions
  * Refactor move exception handling into dedicated code blocks
  * Catch specific mysql warnings that we don't care about
  * Create exceptions for:
    * Table already exists
    * What else?
  * Make sure we're using cursor correctly
'''
import MySQLdb
from seneca.seneca_internal.storage.mysql_intermediate import *
import warnings

requires_commit = [ DeleteRows,
                    UpdateRows,
                    InsertRows,
                    AddTableColumn,
                    DropTableColumn,
                    DropTable,
                    CreateTable,
]

class SQLExecutionResult(object):
    @auto_set_fields
    def __init__(self, success, data):
        pass
    def __str__(self):
        return 'SQLExecutionResult(%s)' % str(self.__dict__)


def handle_error(q_type, err):
    return SQLExecutionResult(False, {'error_code': err.args[0],
                                      'error_message': err.args[1]})


def format_result(q_type, cur):
    # TODO: change to make_format_results_function

    def full_data_results(cur):
        keys = [x[0] for x in cur.description]
        data = TabularKVs(keys, cur.fetchall())
        return SQLExecutionResult(True, data)

    def simple_results(cur):
        return SQLExecutionResult(True, None)

    def not_implemented(cur):
        raise Exception('Not implemented')

    def id_count_results(cur):
        return SQLExecutionResult(True,
            { 'last_row_id':cur.lastrowid,
              'row_count':cur.rowcount
            })

    def col_1_row_1_results(cur):
        return SQLExecutionResult(True,cur.fetchone()[0])

    def col_1_values_results(cur):
        return SQLExecutionResult(True, [x[0] for x in cur.fetchall()])

    parser_funcs = { CreateTable: simple_results,
                     DescribeTable: full_data_results,
                     AddTableColumn: simple_results,
                     DropTableColumn: simple_results,
                     InsertRows: id_count_results,
                     UpdateRows: id_count_results,
                     SelectRows: full_data_results,
                     CountUniqueRows: full_data_results,
                     CountRows: col_1_row_1_results,
                     ListTables: col_1_values_results,
                     DeleteRows: id_count_results,
                     DropTable: simple_results,
    }

    assert q_type in parser_funcs, 'Unknown query type.'
    
    return parser_funcs[q_type](cur)


class Executer(object):
    def __init__(self, username, password, db, host, port=3306):
        self.conn = MySQLdb.connect(host=host, user=username, passwd=password,
                                    db=db, port=port)
        self.conn.autocommit = False
        self.cur = self.conn.cursor()

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
            self.cur.execute(query.to_sql())

            if q_type in requires_commit:
                self.conn.commit()

            return format_result(q_type, self.cur)
        except Exception as err:
            # Note: This function may return a formated result, or it may reraise the error
            return handle_error(q_type, err)

    def many(self, queries):
        # TODO: Test the speed on this
        # TODO: Error handling
        # TODO: Test atomicity
        for q in queries:
            self.cur.execute(q.to_sql())
        self.conn.commit()

        return SQLExecutionResult(True, None)

    def raw(self, q_str):
        self.cur.execute(q_str)
        self.conn.commit()

        return SQLExecutionResult(True, None)



def run_tests():
    import configparser
    import os

    #Executer.init_local_noauth_dev()


    settings = configparser.ConfigParser()
    settings._interpolation = configparser.ExtendedInterpolation()
    this_dir = os.path.dirname(__file__)
    settings.read(os.path.join(this_dir, 'test_db_conf.ini'))

    ex = Executer(settings.get('DB', 'username'),
                   settings.get('DB', 'password'),
                   settings.get('DB', 'database'),
                   settings.get('DB', 'hostname'),
                 )

    create_table_query = CreateTable(
          'test_users',
          AutoIncrementColumn('id'),
          [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
            ColumnDefinition('drivers_licence_number', SQLType('VARCHAR', 30), True),
            ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
            ColumnDefinition('balance', SQLType('BIGINT'), False),
    ], if_not_exists=True )

    def ex_p(q):
        r = ex(q)
        print(r)
        return r
    try:
        ex(DropTable('test_users'))
        ex(DropTable('test_users2'))
        ex(DropTable('test_users3'))
    except:
        pass

    ex_p(create_table_query)
    ex_p(DescribeTable('test_users'))
    ex_p(AddTableColumn('test_users', ColumnDefinition('balance2', SQLType('BIGINT'), False)))
    ex_p(DropTableColumn('test_users', 'balance2'))

    ex_p(InsertRows('test_users', ['username', 'first_name', 'balance'],
    [['tester', 'test', 500],
     ['tester2', 'two', 200],
    ]))

    ex_p(InsertRows('test_users', ['username', 'first_name', 'balance'],
    [['tester3', 'test', 500],
     ['tester4', 'two', 200],
    ]))

    ex_p(UpdateRows('test_users',
      QueryCriterion('eq', 'username', 'tester'),
      {'balance': 0}
    ))

    ex_p(SelectRows('test_users', ['username', 'balance'],
      QueryCriterion('gt', 'balance', 10),
      None,
      None,
    ))

    ex_p(CountUniqueRows('test_users', 'balance', None))
    ex_p(CountRows('test_users', None))

    ex_p(CreateTable('test_users2', AutoIncrementColumn('id'), [], if_not_exists=True))
    ex_p(ListTables(None))
    ex_p(DeleteRows('test_users', QueryCriterion('eq', 'username', 'tester')))

    ex_p(DropTableColumn('test_users', 'balance2'))
    ex_p(CreateTable('test_users2', AutoIncrementColumn('id'), [], if_not_exists=False))

    print(ex.many([


        CreateTable(
              'test_users3',
              AutoIncrementColumn('id'),
              [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
                ColumnDefinition('drivers_licence_number', SQLType('VARCHAR', 30), True),
                ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
                ColumnDefinition('balance', SQLType('BIGINT'), False),
        ], if_not_exists=False),

        InsertRows('test_users3', ['username', 'first_name', 'balance'],
        [['tester1', 'test', 500],
         ['tester2', 'two', 200],
         ['tester3', 'two', 200],
         ['tester4', 'two', 200],
         ['tester5', 'two', 200],
         ['tester6', 'two', 200],
        ]),

        ]))
