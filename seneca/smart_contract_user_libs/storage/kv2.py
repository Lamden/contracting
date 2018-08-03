'''
## TODO:
* Generate name for table
* Create table if not exists
* Serialize/deserialize data
* Hide the resulting table from tabular
'''
import json

from seneca.engine.storage.easy_db import Column, Table, str_len
from seneca.engine.util import auto_set_fields

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


class kv2(object):
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

kv2_obj = kv2()
exports = kv2_obj

def run_tests(deps_provider):
    '''
    >>> print(bool(ex))
    True
    >>> print(bool(name_space))
    True

    >>> kv_obj = kv2()
    >>> print(type(kv_obj))
    <class 'seneca.smart_contract_user_libs.storage.kv2.kv2'>

    >>> _ = print(kv_obj['x'])
    None

    >>> kv_obj['x'] = 5
    >>> print(kv_obj['x'])
    5

    >>> kv_obj['x'] = 6
    >>> print(kv_obj['x'])
    6
    '''
    global name_space, ex
    import doctest, sys
    from seneca.engine.storage.mysql_executer import Executer
    name_space = 'test_tabular'
    ex = deps_provider(Executer)

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
