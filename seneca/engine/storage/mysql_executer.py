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
  * Construct executer from existing connection (mainly for testing)
'''
import MySQLdb
from seneca.engine.storage.mysql_intermediate import *
import warnings

requires_commit = [ DeleteRows,
                    UpdateRows,
                    SetRows,
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
                     SetRows: id_count_results,
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

    def kill(self):
        self.cur.close()
        self.conn.close()


def run_tests(deps_provider):
    '''
    >>> create_table_query = CreateTable(
    ...      'test_users',
    ...      AutoIncrementColumn('id'),
    ...      [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
    ...        ColumnDefinition('drivers_licence_number', SQLType('VARCHAR', 30), True),
    ...        ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
    ...        ColumnDefinition('balance', SQLType('BIGINT'), False),
    ... ], if_not_exists=True )

    >>> res = ex(create_table_query)
    >>> res.success
    True
    >>> res.data is None
    True
    >>> res = ex(DescribeTable('test_users'))
    >>> res.success
    True
    >>> res.data
    {'Field': 'id', 'Type': 'bigint(20) unsigned', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment'}
    {'Field': 'username', 'Type': 'varchar(30)', 'Null': 'YES', 'Key': 'UNI', 'Default': None, 'Extra': ''}
    {'Field': 'drivers_licence_number', 'Type': 'varchar(30)', 'Null': 'YES', 'Key': 'UNI', 'Default': None, 'Extra': ''}
    {'Field': 'first_name', 'Type': 'varchar(30)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': ''}
    {'Field': 'balance', 'Type': 'bigint(20)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': ''}

    >>> res = ex(AddTableColumn('test_users', ColumnDefinition('balance2', SQLType('BIGINT'), False)))
    >>> res.success
    True
    >>> res.data == None
    True
    >>> ex(DescribeTable('test_users')).data
    {'Field': 'id', 'Type': 'bigint(20) unsigned', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment'}
    {'Field': 'username', 'Type': 'varchar(30)', 'Null': 'YES', 'Key': 'UNI', 'Default': None, 'Extra': ''}
    {'Field': 'drivers_licence_number', 'Type': 'varchar(30)', 'Null': 'YES', 'Key': 'UNI', 'Default': None, 'Extra': ''}
    {'Field': 'first_name', 'Type': 'varchar(30)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': ''}
    {'Field': 'balance', 'Type': 'bigint(20)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': ''}
    {'Field': 'balance2', 'Type': 'bigint(20)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': ''}

    >>> res = ex(DropTableColumn('test_users', 'balance2'))
    >>> res.data == None
    True
    >>> ex(DropTableColumn('test_users', 'balance2')).success
    False

    >>> res = ex(InsertRows('test_users', ['username', 'first_name', 'balance'],
    ... [['tester', 'test', 500],
    ... ['tester2', 'two', 200],
    ... ]))
    >>> res.success and res.data == {'last_row_id': 1, 'row_count': 2}
    True

    >>> res = ex(UpdateRows('test_users',
    ...  QueryCriterion('eq', 'username', 'tester'),
    ...  {'balance': 0}
    ... ))
    >>> res.success and res.data == {'last_row_id': 0, 'row_count': 1}
    True


    >>> res = ex(SelectRows('test_users', ['username', 'balance'],
    ...   QueryCriterion('gt', 'balance', 10),
    ...   None,
    ...   None,
    ... ))
    >>> res.success
    True
    >>> res.data
    {'username': 'tester2', 'balance': 200}

    >>> res = ex(CountUniqueRows('test_users', 'balance', None))
    >>> res.success
    True
    >>> res.data
    {'balance': 0, '_count': 1}
    {'balance': 200, '_count': 1}

    >>> ex(CountRows('test_users', None)).data
    2

    >>> ex(CreateTable('test_users2', AutoIncrementColumn('id'), [], if_not_exists=True)).data == None
    True

    >>> ex(ListTables(None)).data
    ['test_users', 'test_users2']

    >>> ex(DeleteRows('test_users', QueryCriterion('eq', 'username', 'tester'))).data
    {'last_row_id': 0, 'row_count': 1}

    >>> res = ex.many([
    ...     CreateTable(
    ...           'test_users3',
    ...           AutoIncrementColumn('id'),
    ...           [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
    ...             ColumnDefinition('drivers_licence_number', SQLType('VARCHAR', 30), True),
    ...             ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
    ...             ColumnDefinition('balance', SQLType('BIGINT'), False),
    ...     ], if_not_exists=False),
    ...     InsertRows('test_users3', ['username', 'first_name', 'balance'],
    ...     [['tester1', 'test', 500],
    ...      ['tester2', 'two', 200],
    ...      ['tester3', 'two', 200],
    ...      ['tester4', 'two', 200],
    ...      ['tester5', 'two', 200],
    ...      ['tester6', 'two', 200],
    ...     ]),
    ... ])
    >>> res.data
    >>> res.success
    True
    '''

    import doctest, sys
    from seneca.engine.storage.mysql_executer import Executer
    ex = deps_provider(Executer)

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
