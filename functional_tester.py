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
from execute_sc import execute_contract

contract_file_path = './example_contracts/'




def get_contract_str_from_fs(file_name):
    full_path = os.join(contract_file_path, file_name)
    with open(full_path, 'r') as sc_file:
        sc_str = sc_file.read()
    return sc_str


def ft_module_loader(contract_id):
    # TODO: query where id=id and status=executed
    return runtime_data, contract_str


def store_contract(user_id, contract_id, contract_str):
    # TODO: status should be pending
    # TODO: store in db


def set_contract_status(contract_id, status_str):
    pass


def run_contract_file_as_user(contract_file_name, contract_id, user_id):
    contract_str = get_contract_str_from_fs(contract_file_name)
    store_contract(user_id, contract_id, contract_str)

    global_run_data = {
        'caller_user_id' = user_id,
        'caller_contract_id' = contract_id,
    }

    this_contract_run_data = {
        'author': user_id,
        'execution_datetime': None
    }

    execute_contract(global_run_data, this_contract_run_data, contract_str, is_main=True, module_loader=ft_module_loader)
    # TODO: if successful, set status executed


    return executed_contract_id
