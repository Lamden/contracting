'''This module decorates (in the design pattern sense) the mysql_intermediate
module, adding namespacing.

To convert:
 {'AddTableColumn',
 'CountRows',
 'CountUniqueRows',
 'CreateTable',
 'DeleteRows',
 'DescribeTable',
 'DropTable',
 'DropTableColumn',
 'InsertRows',

 'ListTables', (prefix, not table_name
 'SelectRows',
 'UpdateRows'}


 Just prepend table_name for everything except ListTables
'''

#from seneca.engine.util import run_super_first, auto_set_fields, intercalate
import seneca.engine.storage.mysql_intermediate as m_i


def name_space_isql(prefix, isql_obj):
    # TODO: Implement
    pass
    # Determine what kind of type

    # Run correct conversion

    # Return obj


# In tests, verify coverage of modified module
# : {k for (k,v) in mi.__dict__.items() if type(v) == type and issubclass(v, m_i.Query)}
def run_tests(_):
    '''
    >>> name_space_isql('', None)
    '''
    # TODO: Add teests.
    import doctest, sys, ast
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
