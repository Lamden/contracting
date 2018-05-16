'''
This module decorates mysql_intermediate adding single point in time snapshotting
(SPITS).

It contains additional functions:
* spits_commit()
* spits_rollback()
* spits_purge()
* spits_verify_clean()

TODO: sql escapes
def sql_escapes(s):
    # TODO: make sure everything I need is here.
    import re
    return re.sub("'", "''", s)


Old notes:
* mysql-point-in-time (commit/rollback to PIT)
  * stuff to figure out
    * Does MyRocks store nulls efficiently?
      If no, rollback row data shouldn't live in same table
      * In that case, does myrocks store empty tables efficiently, can it move rows betweeen tables efficiently
        If so, store rollback data in dedicated tables.
  * additional data
    * Rollback/commit instructions table (not specific to any contract)
      * Rollback pending changes
      * Commit changes
    * Duplicate columns in tables, use a disallowed character with label, something like original_data$<column_name>
  * decorates base lib functions
    * select
      * hides restricted data
        * original_data columns
        * soft-deleted rows where rollback_action = undelete
        * soft-deleted columns
        * block access to soft deleted tables

    * insert row
      * Insert normally, but include rollback_action = delete
      * Obviously don't allow data writes to original_data fields
    * delete row
      * If rollback_action is null
        * Set rollback_action = undelete
        * move data to original_data columns (needed for columns with unique constraint)
    * update row
      * If rollback_action is null
        * Set rollback_action = restore
        * move data to original_data columns
    * Add column
      * add drop column x on table y command to rollback table unless column with same name already dropped
        * i.e. if a column is dropped and readded and dropped again in the same scratch window, just throw it out
          * remember this is a point-in-time snapshot, not an undo-stack
    * drop column
      * if column existed before window save with prepended name
    * drop table
      * if table existed before scratch window, move it to a temporary name
  * additional functionality for
    * begin_scratch(window_id)
      * creates scratch_data table if none exists
    * commit_scratch(window_id)
    * rollback_scratch(window_id)
'''



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

import seneca_internal.storage.mysql_intermediate as isql
from seneca_internal.util import run_super_first, auto_set_fields
import re


SPITS_TOKEN = '$_spits_'
SPITS_PRESERVE_TOKEN = SPITS_TOKEN + 'preserve_$'
SPITS_ROLLBACK_COLUMN_NAME = SPITS_TOKEN + 'rollback_strategy_$'
SPITS_ROLLBACK_COLUMN_SQL_TYPE = isql.SQLType('VARCHAR', 30)
SPITS_METADATA_TABLE_NAME = SPITS_TOKEN + 'metadata_$'
valid_strategies = ['rollback_data', 'delete', 'undelete']


def starts_with_spits(string):
    reg = re.compile(r'^%s' % re.escape(SPITS_TOKEN), re.IGNORECASE)
    return bool(reg.match(string))

def contains_only_good_chars(string):
    reg = re.compile(r'^[a-z0-9_]+$')
    return bool(reg.match(string))

def assert_valid_name(string):
    assert not starts_with_spits(string), "Table name dissallowed it would conflict with our mechanism for snapshotting and rollback"
    assert contains_only_good_chars(string), "Only a-z, 0-9 and _ are allowed in table names."


def bind_passthrough(imported_module, name):
    globals()[name] = getattr(imported_module, name)


to_passthrough = [
  'ColumnDefinition',
  'AutoIncrementColumn',
  'QueryCriterion',
  'format_where_clause',
  'SQLType'
]

for p in to_passthrough:
    bind_passthrough(isql, p)


def make_spits_backup_column(col):
    return isql.ColumnDefinition(SPITS_PRESERVE_TOKEN + col.name, col.sql_type, unique=False, nullable=True)


class CreateTable(isql.CreateTable):
    '''
    '''
    @run_super_first
    def __init__(self): #table_name, primary_key_column_def, other_column_defs, if_not_exists=False
        ## Validation ##
        #Make sure table name doesn't contain spits token, and only allowed characters.
        assert_valid_name(self.table_name)
        # Make sure column names don't contain spits token
        all_columns = [self.primary_key_column_def] + self.other_column_defs
        [assert_valid_name(x.name) for x in all_columns]

        spits_backup_columns = [make_spits_backup_column(x) for x in all_columns]
        self.other_column_defs.extend(spits_backup_columns)

        spits_rollback_strategy_column = isql.ColumnDefinition(SPITS_ROLLBACK_COLUMN_NAME, SPITS_ROLLBACK_COLUMN_SQL_TYPE)
        self.other_column_defs.append(spits_rollback_strategy_column)

    @classmethod
    def from_isql(cls, base_query):
        # TODO: make a generic function that does this: map object attributes onto constructor by var name
        return cls(base_query.table_name, base_query.primary_key_column_def, base_query.other_column_defs, base_query.if_not_exists)


    def to_sql(self):
        # TODO: We have to be careful not to overwrite data in the SPITS_METADATA table, make sure there's a unique constraint
        # Alteratively, maybe we just select the oldest reference to th table and always write
        sql_query = '\n'.join([ 'BEGIN',
                      '',
                      isql.InsertRows(SPITS_METADATA_TABLE_NAME, ['table_name', 'rollback_strategy'],
                        [[self.table_name, 'delete'],
                      ]).to_sql(),
                      '',
                      super().to_sql(),
                      '',
                      'COMMIT'
        ])
        return sql_query

class SelectRows(isql.SelectRows):
    '''
    TODO:
    * If *, describe table and populate fields without $spits_preserve$* and spits_rollback_strategy
    * If user manually adds $spits_preserve$* and spits_rollback_strategy, fail.
      * Figure out how to propagte the failure without making the abstraction leaky
    * AND or if none exists, add to criteria 'NOT spits_rollback_strategy=undelete'
    '''
    @run_super_first
    # table_name,column_names,criteria,order_by=None,order_desc=None,limit=None
    def __init__(self):
        assert_valid_name(self.table_name)
        [assert_valid_name(x) for x in self.column_names]
        # TODO assert_valid_name for criteria names and order_by as well.

        filter_undelete_criterion = isql.QueryCriterion('ne', SPITS_ROLLBACK_COLUMN_NAME, 'undelete')
        if self.criteria:
            self.criteria = isql.AndedCriteria([ filter_undelete_criterion,
                                                 self.criteria
                                               ])
        else:
            self.criteria = filter_undelete_criterion

    @classmethod
    def from_isql(cls, base_query):
        # TODO: set correct fields
        # return cls(base_query.table_name, base_query.primary_key_column_def, base_query.other_column_defs, base_query.if_not_exists)
        pass

    def to_sql(self):
        if self.column_names:
            return super().to_sql()
        else:
            # TODO: decide if we actually want this to auto-populate column names from python-side table object data instead
            return '\n'.join([
                # Query database for table columns that aren't spits, prepare a statement and run it.
                # TODO: should probably use UUID for statement name
                # https://universalmaple.blogspot.com/2018/01/select-all-columns-except-one-in.html
                "SET @sql = CONCAT('SELECT ', (SELECT REPLACE(GROUP_CONCAT(COLUMN_NAME), '<OmitColumn>,', '')",
                "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '%s'" % self.table_name,
                "AND TABLE_SCHEMA = database()",
                "AND COLUMN_NAME NOT LIKE '%s%%')" % SPITS_TOKEN,
                ", ' FROM %s');" % self.table_name,
                'PREPARE stmt1 FROM @sql;',
                'EXECUTE stmt1;'
            ])
            # SET group_concat_max_len = big enough value
            # SELECT * FROM information_schema.columns WHERE table_schema = 'seneca_test' and table_name = 'users';
            # Will need something like this:
            #https://universalmaple.blogspot.com/2018/01/select-all-columns-except-one-in.html
            #SET @sql = CONCAT('SELECT ', (SELECT REPLACE(GROUP_CONCAT(COLUMN_NAME), '<OmitColumn>,', '')
            #  FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '<table>' AND TABLE_SCHEMA = '<database>'), ' FROM <table>');
            #
            #PREPARE stmt1 FROM @sql;
            #EXECUTE stmt1;

#SET @sql = CONCAT('SELECT ', (SELECT REPLACE(GROUP_CONCAT(COLUMN_NAME), '<OmitColumn>,', '')
#FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'uses' AND TABLE_SCHEMA = 'seneca_test')




        pass


def run_tests():
    import seneca_internal.storage.easy_db as easy
    import unittest
    from datetime import datetime
    import sys
    # Patch easy_db module, replace base mysql_intermediate with this module
    class ThisModuleProxy(object):
        def __init__(self, **kwargs):
            for (k,v) in kwargs.items():
                setattr(self, k, v)

    module_self = ThisModuleProxy(**globals())
    easy.isql = module_self

    u = easy.Table('users', easy.AutoIncrementColumn('id'),[
        easy.Column('first_name', str),
        easy.Column('last_name', str),
        easy.Column('balance', int),
        easy.Column('creation_date', datetime)
    ])


    def normalize_str(s):
        return " ".join(s.split())

    class TestQueries(unittest.TestCase):

        def assert_str_equiv(self, s1, s2):
            return self.assertEqual(normalize_str(s1),
                                    normalize_str(s2)
                                    )

        def test_create(self):
            self.assert_str_equiv(u.create_table().to_sql(),
                        """BEGIN

                        INSERT INTO $_spits_metadata_$
                        (table_name, rollback_strategy)
                        VALUES
                        ('users', 'delete');

                        CREATE TABLE users (
                        id BIGINT unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        balance BIGINT,
                        creation_date DATETIME,
                        $_spits_preserve_$id BIGINT,
                        $_spits_preserve_$first_name TEXT,
                        $_spits_preserve_$last_name TEXT,
                        $_spits_preserve_$balance BIGINT,
                        $_spits_preserve_$creation_date DATETIME,
                        $_spits_rollback_strategy_$ VARCHAR(30)
                        );

                        COMMIT
                        """
                        )

        def test_select_with_fields(self):
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            self.assert_str_equiv(u.select('first_name', 'last_name').to_sql(),
                        """SELECT first_name, last_name
                           FROM users
                           WHERE $_spits_rollback_strategy_$ != 'undelete';
                        """
                        )

        def test_select_without_fields(self):
            self.maxDiff = None
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            self.assert_str_equiv(u.select().to_sql(),
                        """
                        SET @sql = CONCAT('SELECT ', (SELECT REPLACE(GROUP_CONCAT(COLUMN_NAME), '<OmitColumn>,', '')
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'users' AND TABLE_SCHEMA = database()
                        AND COLUMN_NAME NOT LIKE '$_spits_%') , ' FROM users');
                        PREPARE stmt1 FROM @sql;
                        EXECUTE stmt1;
                        """
                        )




#        def test_simplest_select(self):
#            self.assertEqual(u.select().to_sql(), 'SELECT *\nFROM users;')
#
##        def test_isupper(self):
#            self.assertTrue('FOO'.isupper())
#            self.assertFalse('Foo'.isupper())
#
#        def test_split(self):
#            s = 'hello world'
#            self.assertEqual(s.split(), ['hello', 'world'])
#            # check that s.split fails when the separator is not a string
#            with self.assertRaises(TypeError):
#                s.split(2)
#
#        u.drop_table().run(ex)
#    u.create_table(if_not_exists=True).run(ex)
#    u.select().where(u.first_name != None).run(ex)


    suite = unittest.TestSuite()
    # TODO: discover and add all tests
    suite.addTest(unittest.makeSuite(TestQueries))
    unittest.TextTestRunner(verbosity=1).run(suite)
