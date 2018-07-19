'''
## TODO:
* Generate name for table
* Create table if not exists
* Serialize/deserialize data
* Hide the resulting table from tabular
'''
import json

from seneca.seneca_internal.storage.easy_db import Column, Table, str_len
from seneca.seneca_internal.util import auto_set_fields

# Note: These will be set by execute_sc
ex = None
name_space = None


def generate_kv_table_name(name_space):
    '''
    '''
    return "${name_space}$kv$".format(name_space=name_space)


def generate_kv_table(full_name):
    '''
    '''
    return Table(full_name, Column('key_', str_len(50), True),[
        Column('json_encoded_value', str),
    ])


class kv(object):
    '''
    '''
    def __init__(self):
        self.table = None

    def lazy_table_create(self):
        if not self.table:
            t_name = generate_kv_table_name(name_space)
            self.table = generate_kv_table(t_name)
            self.table.create_table(if_not_exists=True).run(ex)

    def __getitem__(self, k):
        self.lazy_table_create()
        raw = self.table.select('json_encoded_value').where(self.table.key_ == k).run(ex)
        if raw:
            return json.loads(raw[0]['json_encoded_value'])

    def __setitem__(self, k, v):
        self.lazy_table_create()

        j_v = json.dumps(v)

        # TODO: Implement upserts and replace select + insert | update with that
        if self[k]:
            self.table.update({'json_encoded_value': j_v}) \
              .where(self.table.key_ == k).run(ex)
        else:
            self.table.insert([{'key_': k, 'json_encoded_value': j_v}]).run(ex)

exports = kv()

def run_tests():
    '''
    >>> print(bool(ex))
    True
    >>> print(bool(name_space))
    True

    >>> kv1 = kv()
    >>> print(type(kv1))
    <class 'seneca.smart_contract_user_libs.storage.kv2.kv'>

    >>> _ = print(kv1['x'])
    None

    >>> kv1['x'] = 5
    >>> print(kv1['x'])
    5

    >>> kv1['x'] = 6
    >>> print(kv1['x'])
    6
    '''
    global name_space, ex
    import doctest, sys

    from seneca.seneca_internal.storage.mysql_executer import Executer
    import seneca.load_test_conf as lc

    name_space = 'test_tabular'
    ex = Executer(**lc.db_settings)

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
