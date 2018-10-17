'''
* Must start work on Seneca import system so we can inject caller address here.
* Must not be a singleton like standard Python imports because it's very possible this lib will be called by multiple smart contracts in chain and need to give each its own instance

* Need a way tie all mutations smart contract address of caller
  * Probably do not want this for data access

* Outside table foreign table, something
* Warning for queries created and never run. Though the syntax is consistent, and a finalizer like run() is necessary
  for queries created by chained methods, else how would we know to runs a .select() when it's unknown if the author will
  be adding a .where(...) or running it as is.
    * Plugin to traverse the AST, count up queries, then count up run() invocations and warn if they don't add up.

* TODOs
  * Verify this is being called each time it's imported.
  * New executer, sends intermediate query objects to other process
  *
'''

# TODO: XXX: Current implementation is only for running trusted contracts, no security has been implemented.

import seneca.engine.storage.easy_db as db

ex = None
name_space = None

str_len = db.str_len

and_ = db.and_
or_ = db.or_
not_ = db.not_

def add_name_space(t_name):
    assert name_space is not None, "Tabular module namespace has not been set!"
    return name_space + '$' + t_name

class Tabular(object):
    def __init__(self, underlying_obj):
        self.underlying_obj = underlying_obj

        # TODO: Totally not secure for untrusted contracts. Change this completely!!!
        # if type(underlying_obj) == db.Table:
        #    underlying_obj._name = add_name_space(underlying_obj._name)


    def __call__(self, *args, **kwargs):

        if self.underlying_obj.__name__ == 'run':
            assert ex is not None, 'Mysql executer has not been set.'
            return self.underlying_obj(ex)
        else:
            return Tabular(self.underlying_obj(*args, **kwargs))


    def __getattr__(self, name):
        #print('Called getattr with: ', name)
        if name in ('create_table',):
            # restricted
            raise AttributeError()
        if name in ('_name', 'to_sql'):
            # pass through
            return getattr(self.underlying_obj, name)
        elif hasattr(self.underlying_obj, name):
            a = getattr(self.underlying_obj, name)
            if type(a) == db.Column:
                return a
            else:
                return Tabular(a)
        else:
            raise AttributeError()


def create_table(name, column_tuples):
    t = db.Table(add_name_space(name), db.AutoIncrementColumn('id'),
        [db.Column(*x) for x in column_tuples]
    )

    t.create_table(if_not_exists=True).run(ex)
    return Tabular(t)


def drop_table(t_name):
    assert ex is not None, 'Mysql executer has not been set.'
    t = db.Table.from_existing(add_name_space(t_name)).run(ex)
    res = t.drop_table().run(ex)
    t.underlying_obj = None
    return res


def get_table(name):
    assert ex is not None, 'Mysql executer has not been set.'
    return Tabular(db.Table.from_existing(add_name_space(name)).run(ex))


# Disabling add and remove columns not easily supported with Mysql non-transactional DDL

#def add_column(t, c_def):
#    assert ex is not None, 'Mysql executer has not been set.'
#    res = t.underlying_obj.add_column(*c_def).run(ex)
#    # Refresh table definition
#    t.underlying_obj = db.Table.from_existing(t.underlying_obj._name).run(ex)
#    return res
#
#
#def drop_column(t, c_name):
#    assert ex is not None, 'Mysql executer has not been set.'
#    res = t.underlying_obj.drop_column(c_name).run(ex)
#    # Refresh table definition
#    t.underlying_obj = db.Table.from_existing(t.underlying_obj._name).run(ex)
#    return res
#


exports = {
#     'run_batch': run_batch,
    'str_len': str_len,
    'create_table': create_table,
    'get_table': get_table,
    'drop_table': drop_table,
#    'add_column': add_column,
#    'drop_column': drop_column,
}



def run_tests(deps_provider):
    '''
    >>> u = create_table('users', [
    ... ('first_name', str_len(30), True),
    ... ('last_name', str_len(30), True),
    ... ('nick_name', str_len(30)),
    ... ('balance', int)
    ... ])
    >>> type(u) == Tabular
    True

    >>> r = u.select().run()
    >>> len(r)
    0
    >>> type(r) == TabularKVs
    True

    >>> u.insert([
    ... {'first_name': 'Test1','last_name': 'l1','nick_name': '1','balance': 10},
    ... {'first_name': 'Test2','last_name': 'l2','nick_name': '2','balance': 20},
    ... {'first_name': 'Test3','last_name': 'l3','nick_name': '3','balance': 30},
    ... ]).run()
    {'last_row_id': 1, 'row_count': 3}

    >>> u2 = get_table('users')

    >>> print(u.select().where(and_(u.first_name == 'test' , u.last_name == 'test2')).to_sql())
    SELECT *
    FROM test_tabular$users
    WHERE (first_name = 'test' AND last_name = 'test2');
    '''
    ## SETUP ##
    global ex
    global name_space

    import doctest, sys
    from seneca.engine.storage.mysql_base import TabularKVs
    from seneca.engine.storage.mysql_executer import Executer

    # Set mdules global values for tests
    name_space = 'test_tabular'
    ex = deps_provider(Executer)

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
