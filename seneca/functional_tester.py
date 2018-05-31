#!/usr/bin/env python3.6

'''
TODO:
* Determine sequence of steps
* module storage
  * code_str
  * author
  * execution-datetime
  * execution status: pending, executed, failed
* submit module function
* module loader function to pass to parse
'''
import os
import sys
from execute_sc import execute_contract
from datetime import datetime

# TODO: don't know if we should actually be calling seneca libs from both smart contracts and underlying code, consider revision
import seneca.seneca_internal.storage.easy_db as t
from seneca.seneca_internal.storage.mysql_executer import Executer

# Set up database executer
import configparser


settings = configparser.ConfigParser()
settings._interpolation = configparser.ExtendedInterpolation()
this_dir = os.path.dirname(__file__)
db_conf_path = os.path.join(this_dir, 'seneca_internal/storage/test_db_conf.ini')

settings.read(db_conf_path)

# For testing with unauthenticated local mysql instance, use 'Executer.init_local_noauth_dev()' instead.
ex_ = Executer(settings.get('DB', 'username'),
               settings.get('DB', 'password'),
               settings.get('DB', 'database'),
               settings.get('DB', 'hostname'),
              )

def ex(obj):
    print('Running Query:')
    print(obj.to_sql())
    res = ex_(obj)
    print(res)
    print('\n')
    return res



## Setup steps ##
contract_file_path = os.path.join(this_dir, 'example_contracts/')


contract_table = t.Table('smart_contracts',
    t.Column('contract_address', t.str_len(30), True),
    [ t.Column('code_str', str),
      t.Column('author', t.str_len(60)),
      t.Column('execution_datetime', datetime),
      t.Column('execution_status', t.str_len(30)),
    ]
)

try:
    contract_table.drop_table().run(ex)
except Exception as e:
    if e.args[0]['error_code'] == 1051:
        pass
    else:
        raise

contract_table.create_table().run(ex)


def get_contract_str_from_fs(file_name):
    full_path = os.path.join(contract_file_path, file_name)
    with open(full_path, 'r') as sc_file:
        sc_str = sc_file.read()
    return sc_str


def ft_module_loader(contract_id):
    # TODO: query where id=id and status=executed
    return runtime_data, contract_str


def store_contract(contract_str, user_id, contract_address):
    print('starting store function')
    res = contract_table.insert([{
        'contract_address': contract_address,
        'code_str': contract_str,
        'author': user_id,
        'execution_datetime': None,
        'execution_status': 'pending',
    }]).run(ex)

    print(res)

    #return c['last_row_inserted_id']


def finalize_contract_record(contract_id, passed, contract_address):
    if passed:
        payload = {'execution_status': 'executed', 'execution_datetime': datetime.now()}
    else:
        payload = {'execution_status': 'failed'}

    contract_table.update(payload) \
          .where(contract_table.contract_address == contract_id).run(ex)


def run_contract_file_as_user(contract_file_name, user_id, contract_address):
    print('Running contract: %s' % contract_file_name)

    print('Getting contract from fs...')
    contract_str = get_contract_str_from_fs(contract_file_name)

    print('Storing contract in DB...')
    contract_id = store_contract(contract_str, user_id, contract_address)

    global_run_data = {
        'caller_user_id': user_id,
        'caller_contract_id': contract_id,
    }

    this_contract_run_data = {
        'author': user_id,
        'execution_datetime': None,
        'contract_id': contract_address
    }

    try:
        execute_contract(global_run_data, this_contract_run_data, contract_str, is_main=True, module_loader=ft_module_loader, db_executer=ex)
        passed = True
    except:
        passed = False
        finalize_contract_record(contract_address, passed, contract_address)
        raise

    finalize_contract_record(contract_address, passed, contract_address)

    return contract_id

def print_status():
    for r in contract_table.select().run(ex):
        print('contract: ', r['contract_address'])
        print('\tstatus: ', r['execution_status'])
        print('\texecution_datetime: ', r['execution_datetime'])


def main():
    print('\n\n\n\n*** Starting functional testing ***\n')
    run_contract_file_as_user('rbac.seneca', 'this_is_user_id', 'this_is_rbac_contract_id')

    #run_contract_file_as_user('using_rbac_1.seneca', 'this_is_user_id', 'using_rbac_1_id')
    print('Results:')
    print_status()
    print('\n*** Functional testing completed ***')

if __name__ == '__main__':
    main()
