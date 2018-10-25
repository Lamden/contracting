# import redis, ast, marshal, array, copy, inspect, types, uuid, asyncio
# from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SAFE_BUILTINS
# from seneca.logger import SenecaLogger
# from seneca.interface.client.seneca_client import ContractStruct
# from seneca.engine.interpreter import SenecaInterpreter
#
#
# #0. will imports wrap into class methods or these wrappers with a default client (db=0) which redis-client can pass in active_db
# #1. how do we wrap these redis commands in a such a way that they will execute against active_db
#    #also reads if any have to use master_db
#    #also a mode where extra meta data will be added or not?
# #2. Directory structure / code organization
# #3. do we need redis_client or can be merged into seneca_client itself
#
#
# class ImportsSingleton:
#     protected_imports = {}
#
#
# class SenecaExecutor:
#
#     DB_OFFSET = 1
#     PORT = 6379
#
#     def __init__(self, sbb_idx, num_sbb, loop=None, name=None, get_log_fn=None, concurrent_mode=True):
#         self.loop = loop or asyncio.get_event_loop()
#         asyncio.set_event_loop(self.loop)
#
#         name = name or self.__class__.__name__
#         get_log_fn = get_log_fn or SenecaLogger
#         self.log = get_log_fn(name)
#
#         self.sbb_index = sbb_idx
#         self.num_sb_builders = num_sbb
#         self.concurrent_mode = concurrent_mode
#         # use dbs for copies  # todo - explore for namespaces also
#         self.master_db = redis.StrictRedis(host='localhost', port=self.PORT, db=0)
#         self.worker_dbs = []
#         self.pending_dbs = []
#         self.active_db = None  # pull the first one from worker_dbs when ready
#         # add couple of worker dbs - can be done in a loop for max_number_workers
#         self.max_number_workers = 2    # 2 sufficient for now
#         # phases: 1 - execute contracts, 2 - assertion check / status
#         self.phase1 = "sbb_phase1"
#         self.phase2 = "sbb_phase2"
#         self.transaction_keys = []
#         # different clients have to be opened up front (as redis-py doesn't support select)
#         for db_num in range(self.max_number_workers):
#             db_client = redis.StrictRedis(host='localhost', port=self.PORT, db=db_num+self.DB_OFFSET)
#             if sbb_index == 0:
#                 self.reset_db(db_client)
#             self.worker_dbs.append(db_client)
#
#     # Redis data structure
#     # using pseudo do operations - need to translate to Redis commands later
#     # Organized as 3 major data structures:
#     # data structure 1 - common - all sub-block-builders can write into this one.
#     #      "Common":  {
#     #                    db-key1 : value1,   (value here is same as the one in current master-db
#     #                    ...
#     #                 }
#     # data structure2 - individual ones for each sub-block - only that sub-block will read/write to it
#     #       "sbb_i": {
#     #                    "executed": {
#     #                                    db-key1: orig-value mod-value
#     #                                    ...
#     #                                }
#     #                    "order_key_list": [ [keya keyb .. ] [keyp keyb ..]  ]  - each sub-list will correspond to one txn
#     #                    "status": [ [output, status] ... ]
#     #                }
#     # data structure3 - synchronization variables - all can increment the counters
#     #       "sbb_phase1": 0
#     #       "sbb_phase2": 0
#
#     def set_phase_variables(self, db):
#         pass
#         # TODO
#         # db.set(self.phase1, 0)
#         # db.set(self.phase2, 0)
#
#     def incr_phase_variable(self, db, key):
#         pass
#         # TODO
#         # db.incr(key)
#
#     def get_phase_variable(self, db, key):
#         pass
#         # TODO
#         # return db.get(key)
#
#     def synchronize_phase(self, db, key):
#         while self.get_phase_variable(from_db, key) < self.num_sb_builders:
#             time.sleep(1)                    # right now, just wait
#
#     def wait_my_turn(self, db, key):
#         while self.get_phase_variable(from_db, key) < self.sbb_index:
#             time.sleep(1)                    # right now, just wait
#         assert self.get_phase_variable(from_db, key) == self.sbb_index
#
#
#     def reset_db(self, db):
#         db.flushdb()
#         self.set_phase_variables(db)
#
#
#     def update_master_db(self, from_db):
#         # assert self.get_phase_variable(from_db, self.phase2) == self.num_sb_builders
#         self.synchronize_phase(from_db, self.phase2)
#         # TODO from from_db, get each k,v and update the corresponding entries in master_db
#         pass
#
#     # will be called upon the receipt of new-block-notification
#     # do we want to pass in the input hash or result hash?? --davis
#     def flush(self, input_hash=None, result_hash=None, update_state=True):
#         """
#         If update_state is True, this will also commit the changes
#         to the database. Otherwise, this method will discard any changes
#         """
#         f_db = self.pending_dbs.pop(0)
#         if self.sbb_index == 0:   # only one will do merging db work for now (but it could be the one that is not reponsible for sb)
#             if update_state:
#                 # TODO make sure f_db is the one by matching input_hash(es) ?
#                 self.update_master_db(f_db)
#             self.reset_db(f_db)
#         # do this way only when there is a chance of reusing this db right away. right now, we have two spares and we don't go beyond one block
#         # update synchronization variable  - not needed these commented ones anymore
#         # the last one will do the following
#         # if is_last_one:
#             # self.reset_db(f_db)
#         self.worker_dbs.append(f_db)
#
#     def _start_next_sb(self):
#         if len(self.worker_dbs) == 0:
#             # TODO log error as this shouldn't happen in current flow
#             return False
#         self.active_db = self.worker_dbs.pop(0)
#         # TODO add input-bag hash
#         return True
#
#     def _end_sb(self):
#         self.incr_phase_variable(self.active_db, self.phase1)
#         self.pending_dbs.append(self.active_db)
#         self.active_db = None      # we really don't care, but might be useful initially for error checking
#
#     def merge_sub_block(self, db):
#         pass
#         # order_key_list = db.get_order_key_list
#         # for ord_no, key_list in enumerate(order_key_list):
#         #     modified = False
#         #     for key in key_list:
#         #         orig_value = db."common".get(key)
#         #         my_orig_value = db."sbb_{}".format(sbb_index).get_orig_value(key)
#         #         if my_orig_value != orig_value:
#         #             modified = True
#         #             db."sbb_{}".format(sbb_index).set(key, orig_value)
#         #     if modified:
#         #         re-execute-contract
#         #     for key in key_list:
#         #         mod_value = db."sbb_{}".format(sbb_index).get_mod_value(key)
#         #         db."common".set(key, mod_value)
#
#
#
#     def _make_next_sb(self):
#         f_db = self.pending_dbs.get(0)    # get the first one, but still leave it in the pending_dbs too
#         # assert self.get_phase_variable(f_db, self.phase1) == self.num_sb_builders
#         self.synchronize_phase(f_db, self.phase1)
#         self.wait_my_turn(f_db, self.phase2)
#         txns = self.merge_sub_block(f_db)
#         self.incr_phase_variable(self.f_db, self.phase2)
#         return txns
#
#     # assuming _execute will use these db_read and db_write for db_operations
#     def db_read(self, db, key):
#         pass
#         # if db."common".key.exists:
#               return db."common".key.value
#         # value = fetch key from self.master_db and add to db."common"
#         # return value
#
#     def db_write(self, db, key, value):
#         pass
#         # orig_val = db_read(db, key)
#         # db."sbb_{}".format(self.sbb_index) -> key: orig_value: orig_val, mod_value: value
#         # self.transaction_keys.append(key)
#
#     def _pre_execution(self):
#         self.transaction_keys = []
#
#     def _post_execution(self):
#         pass
#         # self.active_db."sbb_{}".format(self.sbb_index) -> "order_key_list".append(self.transaction_keys)
#         # self.active_db."sbb_{}".format(self.sbb_index) -> incr(num_txns)
#
#     def _execute(self, code_obj):
#         pass
#         # diverts all db_read and db_writes to above
#         # output, state = __execute(code_obj)
#         # return output, state
#
#     def run_contract(self, contract):
#         pass
#
#         # TODO simplify this.
#         # If we assume contract has the contract_name/func_name/args+kwargs, we should be able to do a single
#         # 'execute' call on the SenecaInterpreter, and pass in any necessary bookkeeping information
#         # if SenecaInterpreter.code_obj_exists(contract.get_full_name()):
#         #     code_obj = SenecaInterpreter.get_code_obj(contract.get_full_name())
#         # else:
#         #     tree = SenecaInterpreter.parse_ast(contract.get_code_str())
#         #     code_obj = compile(tree, filename='__main__', mode="exec")
#         #     SenecaInterpreter.set_code_obj(contract.get_full_name(), code_obj)
#         # self._pre_execution(contract)
#         # output, state = self._execute(code_obj)
#         # self.active_db."sbb_{}".format(self.sbb_index)."transactions"."{}".format(contract.order_idx) -> [contract.get_code_str(), output, state]
#         # self._post_execution()
#
#
# class ScopeParser:
#     @property
#     def namespace(self):
#         return inspect.stack()[2].filename.replace('.sen.py', '').split('/')[-1]
#
#
# class Export:
#     def __call__(self, fn, *args, **kwargs):
#         def _fn():
#             return fn(*args, **kwargs)
#         return _fn
#
#
# class Protected(ScopeParser):
#     def __call__(self, fn, *args, **kwargs):
#         module = '.'.join([fn.__module__ or '', fn.__name__])
#         ImportsSingleton.protected_imports[module] = 'protected'
#         # self.imports[module] = 'protected'
#         def _fn():
#             if self.namespace in fn.__module__.split('.')[-1]:
#                 return fn(*args, **kwargs)
#             raise ImportError('"{}" is __protected__ and cannot be imported'.format(module))
#         return _fn
