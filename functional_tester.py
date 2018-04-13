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
import seneca.storage.tabular as t


## Setup steps ##
contract_file_path = './example_contracts/'

t.drop_table('smart_contracts')

contract_table = t.Table('smart_contracts', [
    ('contract_address', t.str_len(30), True),
    ('code_str', str),
    ('author', t.str_len(60)),
    ('execution_datetime', datetime),
    ('execution_status', t.str_len(30)),
])
## End setup ##


def get_contract_str_from_fs(file_name):
    full_path = os.path.join(contract_file_path, file_name)
    with open(full_path, 'r') as sc_file:
        sc_str = sc_file.read()
    return sc_str


def ft_module_loader(contract_id):
    # TODO: query where id=id and status=executed
    return runtime_data, contract_str


def store_contract(contract_str, user_id, contract_address):
    c = contract_table.insert([{
        'contract_address': contract_address,
        'code_str': contract_str,
        'author': user_id,
        'execution_datetime': None,
        'execution_status': 'pending',
    }]).run()

    return c['last_row_inserted_id']



def finalize_contract_record(contract_id, passed, contract_address):
    if passed:
        contract_table.update({'execution_status': 'executed', 'execution_datetime': datetime.now()}) \
          .where_equals('contract_address', contract_id).run()
    else:
        contract_table.update({'execution_status': 'failed'}) \
          .where_equals('contract_address', contract_id).run()




def run_contract_file_as_user(contract_file_name, user_id, contract_address):
    print('Running contract: %s' % contract_file_name)
    contract_str = get_contract_str_from_fs(contract_file_name)

    contract_id = store_contract(contract_str, user_id, contract_address)

    global_run_data = {
        'caller_user_id': user_id,
        'caller_contract_id': contract_id,
    }

    this_contract_run_data = {
        'author': user_id,
        'execution_datetime': None
    }

    try:
        execute_contract(global_run_data, this_contract_run_data, contract_str, is_main=True, module_loader=ft_module_loader)
        passed = True
    except:
        passed = False
        finalize_contract_record(contract_address, passed, contract_address)
        raise

    finalize_contract_record(contract_address, passed, contract_address)

    return contract_id

def print_status():
    for r in contract_table.select().all_rows().run():
        print('contract: ', r['contract_address'])
        print('\tstatus: ', r['execution_status'])
        print('\texecution_datetime: ', r['execution_datetime'])

if __name__ == '__main__':
    print('\n\n\n\n*** Starting functional testing ***\n')
    run_contract_file_as_user('rbac.seneca', 'test_user_1', 'simple')

    print('Results:')
    print_status()
    print('\n*** Functional testing completed ***')
