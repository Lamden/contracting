'''
* Must start work on Seneca import system so we can inject caller address here.
* Must not be a singleton like standard Python imports because it's very possible this lib will be called by multiple smart contracts in chain and need to give each its own instance

* Need a way tie all mutations smart contract address of caller
  * Probably do not want this for data access

* Outside table foreign table, something
* Warning for queries created and never run. Though the syntax is consistent, and a finalizer like run() is necessary
  for queries created by chained methods, else how would we know to runs a .select() when it's unknown if the author will
  be adding a .where_equals() or running as is.
    * Plugin to traverse the AST, count up queries, then count up run() invocations and warn if they don't add up.

* TODOs
  * Verify this is being called each time it's imported.
  * New executer, sends intermediate query objects to other process
  *
'''

import seneca_internal.storage.easy_db as db
import datetime



def run_tests():

    db.execute_sql_query = print
    u = db.Table('users', db.AutoIncrementColumn('id'),[
        db.Column('first_name', str),
        db.Column('last_name', str),
        db.Column('balance', int),
        db.Column('creation_date', datetime)
    ])

    u.create_table(if_not_exists=True).run()




#
#
# def require_constraint_on_run(f):
#     '''Function decorator: useful for query methods, which would be bad to run
#     accidentally when applied to all rows, i.e. updates and deletes'''
#     def ret(obj):
#         assert list(obj.get_constraints()), "To prevent unintended modification to all rows, \
#         destructive opperations must always contain a constraint, either 'where_*(...)', or to modify \
#         all rows, use .update(...).all_rows()"
#
#         return f(obj)
#
#     return ret
#
#
#
# exports = {
#     'outside_table': outside_table,
#     'run_batch': run_batch,
#     'str_len': str_len,
#     'create_table': create_table,
#     'drop_table': drop_table,
#     'add_column': add_column,
#     'drop_column': drop_column,
#     'get_table': get_table
# }
