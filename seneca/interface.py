from seneca.engine.storage.mysql_executer import Executer
from seneca.engine.storage.mysql_spits_executer import Executer as Spits
# a
# class Driver:
#     def __init__(self, username, password, database, port):
#         self.ex = None
#         self.spex = None
#
#     def submit(self, smart_contract: str, sender: str):
#
#         pass
#
#     def flush(self):
#         pass
#
#     def load_director(self, directory):
#         pass
#
#
# def _ex_contract(executor, contract_table, contract_id: str = '', user_id: str='', code_str: str = '',
#                  get_contract=False):
#     assert bool(contract_id) ^ bool(
#         code_str), "Either contract_id or code_str must be passed in (XOR, one or the other)"
#     # log.debug("[inside _execute_contract] Executing contract with id {} and user_id {}".format(contract_id, user_id))
#
#     if code_str:
#         author = user_id
#         exec_dt = None  # todo make this current datetime
#     else:
#         author, exec_dt, code_str = _lookup_contract_info(executor, contract_table, contract_id)
#
#     global_run_data = {'caller_user_id': user_id, 'execution_datetime': exec_dt, 'caller_contract_id': contract_id}
#     this_contract_run_data = {'author': author, 'execution_datetime': exec_dt, 'contract_id': contract_id}
#
#     _ex_func = get_exports if get_contract else execute_contract
#     result = _ex_func(global_run_data, this_contract_run_data, code_str,
#                       module_loader=module_loader_fn(executor, contract_table),
#                       db_executer=executor)
#
#     return result

# ex = Executer('seneca_test', 'ox5rnhhzcenc', 'seneca_test', '127.0.0.1')
