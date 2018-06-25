# Placeholder

# Will create a table with 3 columns for each contract:
# * key (string, unique)
# * value (serialized to string regardless of type)
# * type info
# always upsert

import seneca.seneca_internal.storage.easy_db as db
import datetime

ex = None
name_space = 'kv_test'

str_len = db.str_len

def add_name_space(t_name):
    assert name_space is not None, "KV module namespace has not been set!"
    return name_space + '$' + t_name

class KV(object):
    def __init__(self, underlying_obj):
        self.underlying_obj = underlying_obj

        # TODO: Totally not secure for untrusted contracts. Change this completely!!!
        #if type(underlying_obj) == db.Table:
        #    underlying_obj._name = add_name_space(underlying_obj._name)


    def __call__(self, *args, **kwargs):
        if self.underlying_obj.__name__ == 'run':
            assert ex is not None, 'Mysql executer has not been set.'
            return self.underlying_obj(ex)
        else:
            return KV(self.underlying_obj(*args, **kwargs))

    def __getattr__(self, name):
        #print('Called getattr with: ', name)
        whitelist = ('set', 'run', 'get')
        if name in ('create_table',):
            # restricted
            raise AttributeError('Restricted')
        if name in ('_name', 'to_sql'):
            # pass through
            return getattr(self.underlying_obj, name)
        elif hasattr(self.underlying_obj, name):
            a = getattr(self.underlying_obj, name)
            if type(a) == db.Column:
                return a
            else:
                if name in whitelist:
                    return KV(a)
                else:
                    # restricted to upsert only!
                    raise AttributeError('You may only use {} for a KV'.format(whitelist))
        else:
            raise AttributeError('No attribute "{}"'.format(name))

def create_kv(name):
    column_tuples = [
    ('k', str_len(30), True),
    ('v', str_len(30)),
    ('t', str_len(30))
    ]
    t = db.Table(add_name_space(name), db.AutoIncrementColumn('id'),
        [db.Column(*x) for x in column_tuples]
    )
    t.create_table(if_not_exists=True).run(ex)
    return KV(t)


def drop_kv(t_name):
    assert ex is not None, 'Mysql executer has not been set.'
    t = db.Table.from_existing(add_name_space(t_name)).run(ex)
    res = t.drop_table().run(ex)
    t.underlying_obj = None
    return res


def get_kv(name):
    assert ex is not None, 'Mysql executer has not been set.'
    return KV(db.Table.from_existing(add_name_space(name)).run(ex))

exports = {
#     'run_batch': run_batch,
    'str_len': str_len,
    'create_kv': create_kv,
    'get_kv': get_kv,
    'drop_kv': drop_kv,
}


def run_tests():
    ## SETUP ##
    global ex

    import sys, json
    from os.path import abspath, dirname
    import configparser
    from seneca.seneca_internal.storage.mysql_executer import Executer

    settings = configparser.ConfigParser()
    settings._interpolation = configparser.ExtendedInterpolation()
    settings.read(abspath('seneca/seneca_internal/storage/test_db_conf.ini'))

    ex_ = Executer(settings.get('DB', 'username'),
                   settings.get('DB', 'password'),
                   settings.get('DB', 'database'),
                   settings.get('DB', 'hostname'),
                  )

    def ex__(obj):
        print('Running Query:')
        print(obj.to_sql())
        res = ex_(obj)
        print(res)
        print('\n')
        return res

    ex = ex__

    ## END SETUP ##
    print('****** STARTING TESTS ******')

    kv_name = 'policies'
    try: drop_kv(kv_name)
    except: print('No KV "{}" detected, creating...'.format(kv_name))
    try:
        get_kv(kv_name)
        raise
    except Exception as e:
        assert e.args[0]['error_code'] == 1146, 'KV "{}" still exist after dropping'.format(kv_name)
    p = create_kv(kv_name)
    p.set([
        ('hello', 'world', 'string')
    ]).run(ex)

    print(p.get('hello').run(ex))
