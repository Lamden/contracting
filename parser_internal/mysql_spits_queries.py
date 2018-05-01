'''
This module decorates mysql_queries adding single point in time snapshotting
(SPITS).

It contains additional functions:
* spits_commit()
* spits_rollback()
* spits_purge()
* spits_verify_clean()
'''

import mysql_queries as m


def bind_passthrough(imported_module, name):
    globals()[name] = getattr(imported_module, name)


to_passthrough = [
  'ColumnDefinition',
  'AutoIncrementColumn',
  'QueryCriterion',
  'format_where_clause',
]

for p in to_passthrough:
    bind_passthrough(m, p)


'''
Need additional query features: aggregated criteria, list tables should be more flexible
Other features needed: batched execution

class CreateTable(object):
    * Validation
      * Make sure table name doesn't contain spits token
      * Make sure column names don't contain spits token
    * Write rollback command delete table to spits table
    * Append column definitions, duplicate everything prepended with spits token, $spits_preserve$_ (or something)
    * Append column definitions with spits_rollback_strategy column
    * Create table

class DeleteRows(object):
    * Add deleted flag to spits_rollback_strategy column

class UpdateRows(object):
    * If spits_rollback_stategy is empty
      * copy original columns to $spits_preserve$ columns
      * set spits_rollback_strategy column to recover flag
    * else update in place

class InsertRows(object):
    * Insert normally but set $spits_rollback_strategy$ to 'delete'

class SelectRows(object):
    * If *, describe table and populate fields without $spits_preserve$* and spits_rollback_strategy
    * If user manually adds $spits_preserve$* and spits_rollback_strategy, fail.
      * Figure out how to propagte the failure without making the abstraction leaky
    * AND or if none exists, add to criteria 'NOT spits_rollback_strategy=undelete'

class DescribeTable(object):
    * Describe normally, but omit $spits_preserve$* and $spits_rollback_strategy$

class ListTables(object):
    * List tables, but omit $spits_deleted$* tables and spits table

class AddTableColumn(object):
    * Add two columns, the requested column and the $spits_preserve$_ column
    * Add delete column command to spits table

class DropTableColumn(object):
    * rename column $spits_deleted$_
    * Add undelete column command to spits table

class DropTable(object):
    * move to $spits_deleted$_
'''




if __name__ == '__main__':
    print(CreateTable(
      'test_users',
      AutoIncrementColumn('id'),
      [ ColumnDefinition('username', SQLType('VARCHAR', 30), True),
        ColumnDefinition('drivers_licence_unmber', SQLType('VARCHAR', 30), True),
        ColumnDefinition('first_name', SQLType('VARCHAR', 30), False),
        ColumnDefinition('balance', SQLType('BIGINT'), False),
      ]
    ).to_sql())

    print(InsertRows('test_users', ['username', 'first_name', 'balance'],
        [['tester', 'test', 500],
         ['tester2', 'two', 200],
        ]).to_sql())

    print(DropTable('test_users').to_sql())

    print(SelectRows('test_users', [], None, None, None).to_sql())
    print(SelectRows('test_users', [],
      QueryCriterion('equals', 'username', 'tester'),
      None,
      None,
    ).to_sql())

    print(SelectRows('test_users', [],
      QueryCriterion('gt', 'balance', 10),
      None,
      None,
    ).to_sql())

    print(SelectRows('test_users', ['username', 'balance'],
      QueryCriterion('gt', 'balance', 10),
      None,
      None,
    ).to_sql())

    print(SelectRows('test_users', ['username', 'balance'],
      QueryCriterion('gt', 'balance', 10),
      'balance',
      None,
    ).to_sql())

    print(SelectRows('test_users', ['username', 'balance'],
      QueryCriterion('gt', 'balance', 10),
      None,
      5,
    ).to_sql())

    print(SelectRows('test_users', ['username', 'balance'],
      QueryCriterion('gt', 'balance', 10),
      'balance',
      5,
    ).to_sql())

    print(UpdateRows('test_users',
      QueryCriterion('equals', 'username', 'tester'),
      {'balance': 0, 'status':'broke'}
    ).to_sql())

    print(ListTables(None).to_sql())
    print(ListTables('tester_').to_sql())

    print(DescribeTable('test_users').to_sql())

    print(AddTableColumn('test_users', ColumnDefinition('balance2', SQLType('BIGINT'), False)).to_sql())
    print(AddTableColumn('test_users', ColumnDefinition('secondary_id', SQLType('VARCHAR', 30), True)).to_sql())
    print(DropTableColumn('test_users', 'balance2').to_sql())

    print(DeleteRows('test_users', QueryCriterion('equals', 'username', 'test')).to_sql())
