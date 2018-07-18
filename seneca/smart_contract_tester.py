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

import seneca.seneca_internal.storage.easy_db as t
from seneca.seneca_internal.storage.mysql_executer import Executer

ex_ = None


def run_tests():
    # Intentionally left blank, this file doesn't have any tests.
    pass


def show(*args, **kwargs):
    print('FT:', *args, **kwargs)


def ex(obj):
    res = ex_(obj)
    return res


def set_up():
    global ex_, contract_table
    import load_test_conf as lc

    this_dir = os.path.dirname(__file__)

    ex_ = Executer(**lc.db_settings)

    ## Setup steps ##
    contract_file_path = os.path.join(this_dir, 'example_contracts/')

    try:
        ex_.raw('drop database seneca_test;')
    except Exception as e:
        if e.args[0]['error_code'] == 1046:
            pass
        else:
            raise

    ex_.raw('create database seneca_test;')
    ex_.raw('use seneca_test;')

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


def get_contract_str_from_fs(full_path):
    #full_path = os.path.join(contract_file_path, file_name)
    with open(full_path, 'r') as sc_file:
        sc_str = sc_file.read()
    return sc_str


def ft_module_loader(contract_id):
    # TODO: query where id=id and status=executed
    cs = contract_table.select().where(contract_table.contract_address == contract_id).run(ex)
    c = cs[0]

    runtime_data = {
        'author': c['author'],
        'execution_datetime': c['execution_datetime'],
        'contract_id': c['contract_address']
    }

    return runtime_data, c['code_str']


def store_contract(contract_str, user_id, contract_address):
    res = contract_table.insert([{
        'contract_address': contract_address,
        'code_str': contract_str,
        'author': user_id,
        'execution_datetime': None,
        'execution_status': 'pending',
    }]).run(ex)

    return contract_address


def finalize_contract_record(contract_id, passed, contract_address):
    if passed:
        payload = {'execution_status': 'executed', 'execution_datetime': datetime.now()}
    else:
        payload = {'execution_status': 'failed'}

    contract_table.update(payload) \
          .where(contract_table.contract_address == contract_id).run(ex)


def run_contract_file_as_user(contract_file_name, user_id, contract_address):
    show('Running contract: %s' % contract_file_name)

    show('Getting contract from fs...')
    contract_str = get_contract_str_from_fs(contract_file_name)

    show('Storing contract in DB...')
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
        res = execute_contract(global_run_data, this_contract_run_data, contract_str, is_main=True, module_loader=ft_module_loader, db_executer=ex)
    except:
        show("ERROR: Failure in contract executer (not specifically the contract).")
        finalize_contract_record(contract_address, False, contract_address)
        raise

    finalize_contract_record(contract_address, res.passed, contract_address)

    show("Contract run completed status:", res, "\n\n")
    if not res:
        show(":-(")

    return contract_id

def run_contract(contract_file):
        show('*** Contract:', contract_file)
        contract_id = contract_file.split('/')[-1].split('.')[0]

        run_contract_file_as_user(contract_file, 'this_is_user_id', contract_id)
