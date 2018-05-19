'''
This module decorates (in the design pattern sense) the mysql_intermediate
module, adding single point in time snapshotting (SPITS).

It contains additional functions:
* spits_commit()
* spits_rollback()
* spits_purge()
* spits_verify_clean()
* intialize?

NOTE: Allowing non-nullable constraints in tables will break this lib. When
non-nullable constrain is combined with unique, soft delete becomes untennable,
we'd need to generate a random value to populate the field and hope it didn't collide with
future inserts, or track it and if there was a collision, update it. Much better
to just implmentent non-nullable fields outside the database code, i.e. client-side.

Future Performance Improvements:
* Currently this module is stateless. By going to a stateful model we could cache:
  * table definitions (columns)
  * cache flags marking both rows and tables as dirty
* Stored procedures would probably be more efficient
* Perf-related questions
  * Does MyRocks store nulls efficiently?
    If no, rollback row data shouldn't live in same table
    * In that case, does myrocks store empty tables efficiently, can it move rows betweeen tables efficiently
      If so, store rollback data in dedicated tables.

TODO: Make sure to constrain schema queries with database name
TODO: Check out table_type = 'BASE TABLE' in schema queries
TODO: max_prepared_stmt_count
TODO: Consider doing everything as prepared statements
TODO: Consider doing everything as stored procedures
TODO: sql escapes
def sql_escapes(s):
    # TODO: make sure everything I need is here.
    import re
    return re.sub("'", "''", s)

TODO: figure out how to handle auto_increment after a rollback.
  ALTER TABLE table_name AUTO_INCREMENT = 1;
'''
import re

import seneca_internal.storage.mysql_intermediate as isql
from seneca_internal.util import run_super_first, auto_set_fields, intercalate
from seneca_internal.storage.mysql_base import TabularKVs
from functools import wraps

SPITS_TOKEN = '$_spits_'
SPITS_PRESERVE_TOKEN = SPITS_TOKEN + 'preserve_$'
SPITS_ROLLBACK_COLUMN_NAME = SPITS_TOKEN + 'rollback_strategy_$'
SPITS_ROLLBACK_COLUMN_SQL_TYPE = isql.SQLType('VARCHAR', 30)
SPITS_SOFT_DELETE_PREFIX = SPITS_TOKEN + 'soft_delete_$' # Type not needed.
SPITS_METADATA_TABLE_NAME = SPITS_TOKEN + 'metadata_$'
valid_table_data_level_strategies = ['restore_data', 'delete', 'undelete']
valid_table_schema_level_stratgies = ['restore_data', 'delete', 'undelete']


def spits_commit():
    pass


def spits_rollback():
    pass


def spits_purge():
    pass


def spits_verify_clean():
    pass


def spits_initialize():
    pass


def starts_with_spits(string):
    reg = re.compile(r'^%s' % re.escape(SPITS_TOKEN), re.IGNORECASE)
    return bool(reg.match(string))


def contains_only_good_chars(string):
    reg = re.compile(r'^[a-z0-9_]+$')
    return bool(reg.match(string))


def assert_valid_name(string):
    assert not starts_with_spits(string), "Table name dissallowed it would conflict with our mechanism for snapshotting and rollback"
    assert contains_only_good_chars(string), "Only a-z, 0-9 and _ are allowed in table names."


# Binding some names directly from mysql_intermediate (they need no decoration)
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
# End of direct binding


def make_spits_backup_column(col):
    # NOTE: unique is hardcoded false, this isn't strictly necessary, single
    # point in time means that data can only be moved from the origin column to
    # the backup column, newly written data that is deleted during spits
    # transaction that is deleted is not preserved in back up columns. Remember
    # This isn't a stack of undos, it's just a way to get back to a predefined
    # point in time.
    return isql.ColumnDefinition(SPITS_PRESERVE_TOKEN + col.name, col.sql_type, unique=False)


class CreateTable(isql.CreateTable):
    '''
    class CreateTable(object):
        * Validation
          * Make sure table name doesn't contain spits token
          * Make sure column names don't contain spits token
        * Write rollback command delete table to spits table
        * Append column definitions, duplicate everything prepended with spits token, $spits_preserve_$ (or something)
        * Create table
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

        spits_soft_delete_column = isql.NonNullableBooleanColumn(SPITS_SOFT_DELETE_PREFIX)
        self.other_column_defs.append(spits_soft_delete_column)

        spits_rollback_strategy_column = isql.ColumnDefinition(SPITS_ROLLBACK_COLUMN_NAME, SPITS_ROLLBACK_COLUMN_SQL_TYPE)
        self.other_column_defs.append(spits_rollback_strategy_column)


    @classmethod
    def from_isql(cls, base_query):
        # TODO: make a generic function that does this: map object attributes onto constructor by var name
        return cls(base_query.table_name, base_query.primary_key_column_def, base_query.other_column_defs, base_query.if_not_exists)


    def to_sql(self):
        # TODO: We have to be careful not to overwrite data in the SPITS_METADATA table, make sure there's a unique constraint
        # Alteratively, maybe we just select the oldest reference to th table and always write
        sql_query = '\n'.join(['BEGIN',
                      '',
                      isql.InsertRows(SPITS_METADATA_TABLE_NAME, ['table_name', 'rollback_strategy'],
                        [[self.table_name, 'delete'],
                      ]).to_sql(),
                      '',
                      super().to_sql(),
                      '',
                      'COMMIT;'
        ])
        return sql_query


def filter_soft_deleted(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        filter_undelete_criterion = isql.QueryCriterion('ne', SPITS_SOFT_DELETE_PREFIX, True)
        if self.criteria:
            self.criteria = isql.AndedCriteria([ filter_undelete_criterion,
                                                 self.criteria
                                               ])
        else:
            self.criteria = filter_undelete_criterion

        return f(self, *args, **kwargs)
    return wrapper



class SelectRows(isql.SelectRows):
    '''
    * If *, describe table and populate fields without $spits_preserve$* and spits_rollback_strategy
    * If user manually adds $spits_preserve$* and spits_rollback_strategy, fail.
      * Figure out how to propagte the failure without making the abstraction leaky
    * AND or if none exists, add to criteria 'NOT spits_rollback_strategy=undelete'

    * select
      * hides restricted data
        * preserved_data columns
        * soft-deleted rows where rollback_action = undelete
        * soft-deleted columns
        * block access to soft deleted tables
    '''
    @run_super_first
    # table_name,column_names,criteria,order_by=None,order_desc=None,limit=None
    @filter_soft_deleted
    def __init__(self):
        assert_valid_name(self.table_name)
        [assert_valid_name(x) for x in self.column_names]
        # TODO assert_valid_name for criteria names and order_by as well.

    @classmethod
    def from_isql(cls, base_query):
        return cls( base_query.table_name,
                    base_query.column_names,
                    base_query.criteria,
                    base_query.order_by,
                    base_query.order_desc,
                    base_query.limit
                  )

    def to_sql(self):
        if self.column_names:
            return super().to_sql()
        else:
            # TODO: decide if we actually want this to auto-populate column names from python-side table object data instead
            return intercalate('\n', [
                # Query database for table columns that aren't spits, prepare a statement and run it.
                # TODO: should probably use UUID for statement name
                # https://universalmaple.blogspot.com/2018/01/select-all-columns-except-one-in.html
                "SET @sql = CONCAT('SELECT ', (SELECT REPLACE(GROUP_CONCAT(COLUMN_NAME), '<OmitColumn>,', '')",
                "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '%s'" % self.table_name,
                "AND TABLE_SCHEMA = database()",
                "AND COLUMN_NAME NOT LIKE '%s%%')" % SPITS_TOKEN,
                ", '",
                "FROM %s" % self.table_name,
                isql.format_where_clause(self.criteria),
                isql.make_order_by(self.order_by, self.order_desc),
                'LIMIT %d' % self.limit if self.limit else None,
                " ');",
                'PREPARE stmt1 FROM @sql;',
                'EXECUTE stmt1;',
                'DEALLOCATE PREPARE stmt1;',
            ])

class UpdateRows(isql.UpdateRows):
    '''
    * update row
        * If spits_rollback_stategy is empty
          * copy original columns to $spits_preserve$ columns
          * set spits_rollback_strategy column to recover flag
          * Set rollback_action = restore
        * else update in place

        # TODO: Mark table dirty in SPITS_METADATA_TABLE
    '''
    @run_super_first
    @filter_soft_deleted
    def __init__(self):
        assert_valid_name(self.table_name)
        [assert_valid_name(x) for x in self.column_value_dict.keys()]
        # TODO: assert_valid_name for criteria names and order_by as well.


    @classmethod
    def from_isql(cls, base_query):
        #table_name, criteria, column_value_dict, order_by=None, order_desc=None, limit=None
        return cls( base_query.table_name,
                    base_query.criteria,
                    base_query.column_value_dict,
                    base_query.order_by,
                    base_query.order_desc,
                    base_query.limit
                  )

    def to_sql(self):
        new_val_assignments = ',\n'.join(['%s=%s' % (k, isql.cast_py_to_sql(v)) for (k,v) in self.column_value_dict.items()])
        # TODO: See if this can be simplified. Try to wrap whole rollback action in a single case expression.

        rollback_action_assignement = "{SPITS_ROLLBACK_COLUMN_NAME} = CASE WHEN {SPITS_ROLLBACK_COLUMN_NAME} IS NULL \
THEN \\'restore_data\\' ELSE {SPITS_ROLLBACK_COLUMN_NAME} END".format(**locals(),**globals())
        order_by_str = isql.make_order_by(self.order_by, self.order_desc)

        perserve_columns = ' '.join(["SET @preserve_columns = (SELECT REPLACE(GROUP_CONCAT( CONCAT('\n{SPITS_PRESERVE_TOKEN}', ",
        "COLUMN_NAME, ' = CASE WHEN {SPITS_ROLLBACK_COLUMN_NAME} IS NULL THEN ', COLUMN_NAME, '",
        "ELSE {SPITS_PRESERVE_TOKEN}', COLUMN_NAME, ' END') ), '<OmitColumn>,', '')",
        "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self.table_name}' AND TABLE_SCHEMA = database() ",
        "AND COLUMN_NAME not like '{SPITS_TOKEN}%');"]).format(**locals(), **globals())

        second_query = intercalate('\n', ["SET @full_query = CONCAT('UPDATE {self.table_name} SET ',  @preserve_columns, ', ",
        intercalate(',\n',[
            new_val_assignments,
            rollback_action_assignement,
        ]),
        format_where_clause(self.criteria),
        order_by_str,
        'LIMIT %d' % self.limit if self.limit else None,
        "');"
        ]).format(**locals(),**globals())

        prepare_and_execute = intercalate('\n', [
            'PREPARE stmt1 FROM @full_query;',
            'EXECUTE stmt1;',
            'DEALLOCATE PREPARE stmt1;',
        ])

        full_query = intercalate('\n\n', [
            perserve_columns,
            second_query,
            prepare_and_execute,
        ])

        return full_query


class DeleteRows(isql.DeleteRows):
    '''
    * This is a soft delete, actually an implemented as an update query, not a real SQL delete
      * We completely ignore rows that are already deleted (with SPITS RC = undelete)
      * If rollback_action is null
        * then
            * Set rollback_action = undelete
            * copy all original columns to preserve columns
      * set all original columns to null (needed for columns with unique constraint)

    NOTE: As a performance optimization we could consider doing this more simply for tables without any uniqueness constraints
    '''
    @run_super_first
    #self, table_name, criteria, order_by=None, order_desc=None, limit=None
    @filter_soft_deleted
    def __init__(self):
        assert_valid_name(self.table_name)
        # TODO: assert_valid_name for criteria names and order_by as well.
        # TODO: mark table as dirty

    @classmethod
    def from_isql(cls, base_query):
        return cls(base_query.table_name,
                   base_query.criteria,
                   ase_query.order_by,
                   base_query.order_desc,
                   base_query.limit
                  )

    def to_sql(self):
        # TODO: Dedupe from update.

        new_val_assignments = None #',\n'.join(['%s=%s' % (k, isql.cast_py_to_sql(v)) for (k,v) in self.column_value_dict.items()])
        # TODO: See if this can be simplified. Try to wrap whole rollback action in a single case expression.

        rollback_action_assignement = "{SPITS_ROLLBACK_COLUMN_NAME} = CASE WHEN {SPITS_ROLLBACK_COLUMN_NAME} IS NULL \
THEN \\'undelete\\' ELSE {SPITS_ROLLBACK_COLUMN_NAME} END".format(**locals(),**globals())
        order_by_str = isql.make_order_by(self.order_by, self.order_desc)

        perserve_columns = ' '.join(["SET @preserve_columns = (SELECT REPLACE(GROUP_CONCAT( CONCAT('\n{SPITS_PRESERVE_TOKEN}', ",
        "COLUMN_NAME, ' = CASE WHEN {SPITS_ROLLBACK_COLUMN_NAME} IS NULL THEN ', COLUMN_NAME, '",
        # NOTE: unlike UpdateRows, we're additionally setting COLUMN_NAME = NULL
        "ELSE {SPITS_PRESERVE_TOKEN}', COLUMN_NAME, ' END, ',",
        "COLUMN_NAME, ' = NULL' ) ), '<OmitColumn>,', '')",
        "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self.table_name}' AND TABLE_SCHEMA = database() ",
        "AND COLUMN_NAME not like '{SPITS_TOKEN}%');"]).format(**locals(), **globals())

        second_query = intercalate('\n', ["SET @full_query = CONCAT('UPDATE {self.table_name} SET ',  @preserve_columns, ', ",
        intercalate(',\n',[
            new_val_assignments,
            rollback_action_assignement,
        ]),
        format_where_clause(self.criteria),
        order_by_str,
        'LIMIT %d' % self.limit if self.limit else None,
        "');"
        ]).format(**locals(),**globals())

        prepare_and_execute = intercalate('\n', [
            'PREPARE stmt1 FROM @full_query;',
            'EXECUTE stmt1;',
            'DEALLOCATE PREPARE stmt1;',
        ])

        full_query = intercalate('\n\n', [
            perserve_columns,
            second_query,
            prepare_and_execute,
        ])

        return full_query



class InsertRows(isql.InsertRows):
    '''
    * insert row
      * Insert normally, but include rollback_action = delete
      * Obviously don't allow data writes to preserve_data fields
    # TODO: Mark table dirty in SPITS_METADATA_TABLE
    # TODO: if not already entered in SPITS_METADATA_TABLE, get current auto increment and store it.
    '''
    @run_super_first
    # table_name, column_names, list_of_values_lists
    def __init__(self):
        assert_valid_name(self.table_name)
        # Make sure column names don't contain spits token
        [assert_valid_name(x) for x in self.column_names]

        # Append rollback strategy
        self.column_names = list(self.column_names + (SPITS_ROLLBACK_COLUMN_NAME, ))
        self.list_of_values_lists = [list(x + ('delete', )) for x in self.list_of_values_lists]

    @classmethod
    def from_isql(cls, base_query):
        #table_name, column_names, list_of_values_lists
        return cls(base_query.table_name,
                   base_query.column_names,
                   base_query.list_of_values_lists
                  )

    def to_sql(self):
        s = super().to_sql()
        return s


class CountUniqueRows(isql.CountUniqueRows):
    '''
    Similar to methodology for select:
       * Need to filter out soft-deleted rows
       * Need to forbid $spits from
    '''
    @run_super_first
    #self, table_name, unique_column, criteria
    @filter_soft_deleted
    def __init__(self):
        assert_valid_name(self.table_name)
        assert_valid_name(self.unique_column)
        # TODO: assert_valid_name for criteria names and order_by as well.

    @classmethod
    def from_isql(cls, base_query):
        #self, table_name, unique_column, criteria
        return cls(base_query.table_name, base_query.unique_column, base_query.criteria)

    def to_sql(self):
        s = super().to_sql()
        return s


class CountRows(isql.CountRows):
    '''
    Similar to methodology for select:
       * Need to filter out soft-deleted rows
       * Need to forbid $spits from
    '''
    @run_super_first
    #self, table_name, criteria
    @filter_soft_deleted
    def __init__(self):
        assert_valid_name(self.table_name)
        # TODO: assert_valid_name for criteria names and order_by as well.

    @classmethod
    def from_isql(cls, base_query):
        return cls(base_query.table_name, base_query.criteria)

    def to_sql(self):
        s = super().to_sql()
        return s


class DropTable(isql.DropTable):
    '''
    * move to $spits_deleted_$
    * Only if there isn't already and entry that says create
    '''
    @run_super_first
    #self, table_name
    def __init__(self):
        assert_valid_name(self.table_name)
        # TODO: assert_valid_name for criteria names and order_by as well.

    @classmethod
    def from_isql(cls, base_query):
        return cls(base_query.table_name)

    def to_sql(self):
        #https://stackoverflow.com/questions/9279619/mysql-rename-table-if-exists
        soft_delete_table_name = SPITS_SOFT_DELETE_PREFIX + self.table_name
        return """
            BEGIN;
            SELECT Count(*)
            INTO @exists
            FROM information_schema.tables
            WHERE table_name = '{soft_delete_table_name}';

            SET @query = If(@exists = 0,
                'RENAME TABLE {self.table_name} TO {soft_delete_table_name}',
                'SELECT \\'nothing to rename\\' status');

            PREPARE stmt FROM @query;
            EXECUTE stmt;
            COMMIT;
            """.format(**locals())

'''
* Add column
  * add drop column x on table y command to rollback table unless column with same name already dropped
    * i.e. if a column is dropped and readded and dropped again in the same scratch window, just throw it out
      * remember this is a point-in-time snapshot, not an undo-stack
* drop column
  * if column existed before window save with prepended name
* drop table
  * if table existed before scratch window, move it to a temporary name


DescribeTable(self, table_name)
ListTable(prefix)
AddTableColumn(self, table_name, column_def)
DropTableColumn(table_name, column_name)
DropTable(table_name)

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


'''



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
        maxDiff = None

        def assert_str_equiv(self, s1, s2):
            return self.assertEqual(normalize_str(s1),
                                    normalize_str(s2)
                                    )

        def test_create(self):
            self.maxDiff = None
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
                            $_spits_soft_delete_$ Boolean NOT NULL DEFAULT FALSE,
                            $_spits_rollback_strategy_$ VARCHAR(30)
                            );

                            COMMIT;
                        """
                        )

        def test_select_with_fields(self):
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            self.assert_str_equiv(u.select('first_name', 'last_name').to_sql(),
                        """SELECT first_name, last_name
                           FROM users
                           WHERE $_spits_soft_delete_$ != TRUE;
                        """
                        )

        def test_select_without_fields(self):
            self.maxDiff = None
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            self.assert_str_equiv(u.select().to_sql(), """
                        SET @sql = CONCAT('SELECT ', (SELECT REPLACE(GROUP_CONCAT(COLUMN_NAME), '<OmitColumn>,', '')
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'users' AND TABLE_SCHEMA = database()
                        AND COLUMN_NAME NOT LIKE '$_spits_%') , ' FROM users
                        WHERE $_spits_soft_delete_$ != TRUE
                        ');
                        PREPARE stmt1 FROM @sql;
                        EXECUTE stmt1;
                        DEALLOCATE PREPARE stmt1;
                        """
                        )

        def test_select_without_fields_order_and_limit(self):
            self.assert_str_equiv(u.select().order_by('first_name').limit(10).to_sql(), """
                        SET @sql = CONCAT('SELECT ', (SELECT REPLACE(GROUP_CONCAT(COLUMN_NAME), '<OmitColumn>,', '')
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'users' AND TABLE_SCHEMA = database()
                        AND COLUMN_NAME NOT LIKE '$_spits_%') , ' FROM users
                        WHERE $_spits_soft_delete_$ != TRUE
                        ORDER BY first_name
                        LIMIT 10
                        ');
                        PREPARE stmt1 FROM @sql;
                        EXECUTE stmt1;
                        DEALLOCATE PREPARE stmt1;
                        """
                        )

        #TODO: write this test, actually a few
        def test_update(self):
            self.maxDiff = None
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            self.assert_str_equiv(u.update({'balance': 1000}).to_sql(), """
                        SET @preserve_columns = (SELECT REPLACE(GROUP_CONCAT( CONCAT('
                        $_spits_preserve_$',  COLUMN_NAME, ' = CASE WHEN $_spits_rollback_strategy_$ IS NULL THEN ', COLUMN_NAME, ' ELSE $_spits_preserve_$', COLUMN_NAME, ' END') ), '<OmitColumn>,', '') FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'users' AND TABLE_SCHEMA = database()  AND COLUMN_NAME not like '$_spits_%');

                        SET @full_query = CONCAT('UPDATE users SET ',  @preserve_columns, ',
                        balance=1000,
                        $_spits_rollback_strategy_$ = CASE WHEN $_spits_rollback_strategy_$ IS NULL THEN \\'restore_data\\' ELSE $_spits_rollback_strategy_$ END
                        WHERE $_spits_soft_delete_$ != TRUE
                        ');

                        PREPARE stmt1 FROM @full_query;
                        EXECUTE stmt1;
                        DEALLOCATE PREPARE stmt1;
                        """
                        )

        def test_delete(self):
            self.maxDiff = None
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            good_result = """
                SET @preserve_columns = (SELECT REPLACE(GROUP_CONCAT( CONCAT('
                $_spits_preserve_$',  COLUMN_NAME, ' = CASE WHEN $_spits_rollback_strategy_$ IS NULL THEN ', COLUMN_NAME, ' ELSE $_spits_preserve_$', COLUMN_NAME, ' END, ', COLUMN_NAME, ' = NULL' ) ), '<OmitColumn>,', '') FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'users' AND TABLE_SCHEMA = database()  AND COLUMN_NAME not like '$_spits_%');

                SET @full_query = CONCAT('UPDATE users SET ',  @preserve_columns, ',
                $_spits_rollback_strategy_$ = CASE WHEN $_spits_rollback_strategy_$ IS NULL THEN \\'undelete\\' ELSE $_spits_rollback_strategy_$ END
                WHERE $_spits_soft_delete_$ != TRUE
                ');

                PREPARE stmt1 FROM @full_query;
                EXECUTE stmt1;
                DEALLOCATE PREPARE stmt1;
            """
            self.assert_str_equiv(u.delete().to_sql(), good_result)


        def test_insert(self):
            self.maxDiff = None
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            # TODO: Might have to worry about incrementing auto increments
            self.assert_str_equiv(u.insert([
              {'first_name': 'Test', 'last_name': 'User','balance': 0},
              {'first_name': 'Test2', 'last_name': 'User','balance': 0},
              {'first_name': 'Test3', 'last_name': 'User','balance': 0},
            ]).to_sql(), """
                        INSERT INTO users
                        (first_name, last_name, balance, $_spits_rollback_strategy_$)
                        VALUES
                        ('Test', 'User', 0, 'delete'), ('Test2', 'User', 0, 'delete'), ('Test3', 'User', 0, 'delete');
                        """)


            self.assert_str_equiv(u.insert([
              {'first_name': 'Test'},
            ]).to_sql(), """
                        INSERT INTO users
                        (first_name, $_spits_rollback_strategy_$)
                        VALUES
                        ('Test', 'delete');
                        """)


        def test_count_unique(self):
            self.maxDiff = None
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            # TODO: Might have to worry about incrementing auto increments
            self.assert_str_equiv(u.count_unique('first_name').where(u.balance >= 10).to_sql(), """
                        SELECT first_name, COUNT(*) as _count
                        FROM users
                        WHERE ($_spits_soft_delete_$ != TRUE
                           AND balance >= 10)
                        GROUP BY first_name;
                        """)

            self.assert_str_equiv(u.count_unique('first_name').to_sql(), """
                        SELECT first_name, COUNT(*) as _count
                        FROM users
                        WHERE $_spits_soft_delete_$ != TRUE
                        GROUP BY first_name;
                        """)

        def test_count(self):
            self.maxDiff = None
            # NOTE: This is partially just pass-through functionality from base isql
            # The only difference being filtering of soft-deleted rows, and validation
            # That user selected table name, column names, etc. aren't $_spits_
            # TODO: Might have to worry about incrementing auto increments
            self.assert_str_equiv(u.count().where(u.balance >= 10).to_sql(), """
                        SELECT COUNT(*) as _count
                        FROM users
                        WHERE ($_spits_soft_delete_$ != TRUE
                           AND balance >= 10);
                        """)

            self.assert_str_equiv(u.count().to_sql(), """
                        SELECT COUNT(*) as _count
                        FROM users
                        WHERE $_spits_soft_delete_$ != TRUE;
                        """)

        def test_drop_table(self):
            self.assert_str_equiv(u.drop_table().to_sql(),
            """
                        BEGIN;
            SELECT Count(*)
            INTO @exists
            FROM information_schema.tables
            WHERE table_name = '$_spits_soft_delete_$users';

            SET @query = If(@exists = 0,
                'RENAME TABLE users TO $_spits_soft_delete_$users',
                'SELECT \\'nothing to rename\\' status');

            PREPARE stmt FROM @query;
            EXECUTE stmt;
            COMMIT;
            """)





    suite = unittest.TestSuite()
    # TODO: discover and add all tests
    suite.addTest(unittest.makeSuite(TestQueries))
    unittest.TextTestRunner(verbosity=1).run(suite)
