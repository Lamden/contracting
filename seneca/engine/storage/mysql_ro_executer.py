from seneca.engine.util import *
from seneca.engine.storage.mysql_intermediate import *

dissallowed_queries = [ AddTableColumn,
                        DropTableColumn,
                        DeleteRows,
                        UpdateRows,
                        InsertRows,
                        DropTable,
                        CreateTable,
                        SetRows,
]

class Executer(object):
    @auto_set_fields
    def __init__(self, ex):
        pass

    def __call__(self, query):
        type(query)
        assert type(query) not in dissallowed_queries, 'Queries that modify data are not allowed in mysql_ro_executer read only context.'
        return self.ex(query)

    def many(self, queries):
        for q in queries:
            self(q)

    def kill(self):
        return self.ex.kill()


def run_tests(deps_provider):
    pass
    '''
    Clear DB:
    >>> _ = bex.cur.execute('DROP DATABASE seneca_test;')
    >>> _ = bex.cur.execute('CREATE DATABASE seneca_test;')
    >>> _ = bex.cur.execute('use seneca_test;')

    >>> ro_ex = ExecuterBase(bex)

    >>> try_ex_catch(ro_ex, DeleteRows('test_users', QueryCriterion('eq', 'username', 'test')))
    Queries that modify data are not allowed in mysql_ro_executer read only context.
    >>> try_ex_catch(ro_ex, UpdateRows( 'test_users',
    ...                  QueryCriterion('eq', 'username', 'tester'),
    ...                  {'balance': 0, 'status':'broke'}))
    Queries that modify data are not allowed in mysql_ro_executer read only context.
    >>> try_ex_catch(ro_ex, SetRows( 'test_users',
    ...                  [[0, 'broke']]))
    Queries that modify data are not allowed in mysql_ro_executer read only context.
    >>> try_ex_catch(ro_ex, InsertRows('test_users', ['username', 'first_name', 'balance'],
    ...   [['tester', 'test', 500],
    ...    ['tester2', 'two', 200],
    ...   ]))
    Queries that modify data are not allowed in mysql_ro_executer read only context.
    >>> try_ex_catch(ro_ex, InsertRows('test_users', ['username', 'first_name', 'balance'],[['tester', 'test', 500]]))
    Queries that modify data are not allowed in mysql_ro_executer read only context.
    >>> try_ex_catch(ro_ex, DropTableColumn('test_users', 'balance2'))
    Queries that modify data are not allowed in mysql_ro_executer read only context.
    >>> try_ex_catch(ro_ex, DropTable('test_users'))
    Queries that modify data are not allowed in mysql_ro_executer read only context.
    >>> try_ex_catch(ro_ex, ct)
    Queries that modify data are not allowed in mysql_ro_executer read only context.

    Setup some data:
    >>> print(bex(ct))
    SQLExecutionResult({'success': True, 'data': None})

    >>> print(bex(InsertRows('test_users', ['username'],
    ...   [['user_a'],
    ...    ['user_b'],
    ...   ])))
    SQLExecutionResult({'success': True, 'data': {'last_row_id': 1, 'row_count': 2}})

    >>> ro_ex(SelectRows('test_users', [], None, None, None)).success
    True
    >>> ro_ex(CountUniqueRows('test_users', 'id', None)).success
    True
    >>> ro_ex(CountRows('test_users', None)).success
    True
    >>> ro_ex(DescribeTable('test_users')).success
    True
    >>> ro_ex(ListTables()).success
    True
    '''
    import doctest, sys
    from seneca.engine.storage.mysql_executer import Executer
    bex = deps_provider(Executer)

    ct = CreateTable('test_users',
                     AutoIncrementColumn('id'),
                     [ ColumnDefinition('username', SQLType('VARCHAR', 30), True)]
                    )

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
