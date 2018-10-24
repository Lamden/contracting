import redis, ast, marshal, array, copy, inspect, types, uuid, asyncio
from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SAFE_BUILTINS
from seneca.logger import SenecaLogger
from seneca.interface.client.seneca_client import ContractStruct
from seneca.engine.interpreter import SenecaInterpreter


#0. will imports wrap into class methods or these wrappers with a default client (db=0) which redis-client can pass in active_db
#1. how do we wrap these redis commands in a such a way that they will execute against active_db
   #also reads if any have to use master_db
   #also a mode where extra meta data will be added or not?
#2. Directory structure / code organization
#3. do we need redis_client or can be merged into seneca_client itself


class ImportsSingleton:
    protected_imports = {}


class SenecaExecutor:

    DB_OFFSET = 1
    PORT = 6379

    def __init__(self, sb_idx, loop=None, name=None, get_log_fn=None, concurrent_mode=True):
        self.loop = loop or asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

        name = name or self.__class__.__name__
        get_log_fn = get_log_fn or SenecaLogger
        self.log = get_log_fn(name)

        self.sb_index = sb_idx
        self.concurrent_mode = concurrent_mode
        # use dbs for copies  # todo - explore for namespaces also
        # change / pass port number
        self.master_db = redis.StrictRedis(host='localhost', port=self.PORT, db=0)
        self.worker_dbs = []
        self.pending_dbs = []
        self.active_db = None  # pull the first one from worker_dbs when ready
        # add couple of worker dbs - can be done in a loop for max_number_workers
        self.max_number_workers = 2    # 2 sufficient for now
        # different clients have to be opened up front (as redis-py doesn't support select)
        for db_num in range(self.max_number_workers):
            db_client = redis.StrictRedis(host='localhost', port=self.PORT, db=db_num+self.DB_OFFSET)
            self.worker_dbs.append(db_client)

    def update_master_db(self, from_db):
        # from from_db, get each k,v and update the corresponding entries in master_db
        pass

    # will be called upon the receipt of new-block-notification
    # do we want to pass in the input hash or result hash?? --davis
    def flush(self, input_hash=None, result_hash=None, update_state=True):
        """
        If update_state is True, this will also commit the changes
        to the database. Otherwise, this method will discard any changes
        """
        # need to iterate cur_db items and push them to master_db  - same as commit
        # make sure f_db is the one
        # pop the right one (should be first one mostly) from active_dbs
        # save the state to master_db and purge it completely and return it to worker_dbs
        f_db = self.pending_dbs.pop(0)    # actually it has to match result_hash
        sb_data = None
        if update_state:
            sb_data = self.update_master_db(f_db)
        f_db.flushdb()
        self.worker_dbs.append(f_db)
        return sb_data

    def _start_next_sb(self):
        if len(self.worker_dbs) == 0:
            return False
        self.active_db = self.worker_dbs.pop(0)
        # initialize it - add couple of special k-vs
        # input-bag hash ? or result-hash at the end so save can check the right one
        # sync counter ??
        # return true / false so higher level can throttle it the way it want
        # phases: 1 - execute contracts, 2 - assertion check / status
        # if sb_index == 0: then initialize two phase variables (see above) to zeros
        return True

    def _end_sb(self):
        # update the phase info in self.active_db
        pass

    def db_read(self, key):
        pass
        # fetch from master_db

    def db_write(self, key, value):
        pass
        # need to maintain two / three layers of data in cache (worker_db) layer
        # common -> meaning everyone will update the data here. consists of conflict info:
        #           "conflicts":key - <sorted set>  -> (sb_index:order_idx, sb_index * 1000 + order_idx (for score))
        # cache(i):
        #      1.  "value":key - new_set  new_incr  constraint
        #      2.  hash [i] [ txn #] -> [ keys affected ]

    # same as above
    def _post_execution(self):
        pass

    def run_contract(self, contract):
        pass

        # TODO simplify this.
        # If we assume contract has the contract_name/func_name/args+kwargs, we should be able to do a single
        # 'execute' call on the SenecaInterpreter, and pass in any necessary bookkeeping information
        # if SenecaInterpreter.code_obj_exists(contract.get_full_name()):
        #     code_obj = SenecaInterpreter.get_code_obj(contract.get_full_name())
        # else:
        #     tree = SenecaInterpreter.parse_ast(contract.get_code_str())
        #     code_obj = compile(tree, filename='__main__', mode="exec")
        #     SenecaInterpreter.set_code_obj(contract.get_full_name(), code_obj)
        # self._pre_execution(contract)
        # self._execute(code_obj)
        # self._post_execution()


class ScopeParser:
    @property
    def namespace(self):
        return inspect.stack()[2].filename.replace('.sen.py', '').split('/')[-1]


class Export:
    def __call__(self, fn, *args, **kwargs):
        def _fn():
            return fn(*args, **kwargs)
        return _fn


class Protected(ScopeParser):
    def __call__(self, fn, *args, **kwargs):
        module = '.'.join([fn.__module__ or '', fn.__name__])
        ImportsSingleton.protected_imports[module] = 'protected'
        # self.imports[module] = 'protected'
        def _fn():
            if self.namespace in fn.__module__.split('.')[-1]:
                return fn(*args, **kwargs)
            raise ImportError('"{}" is __protected__ and cannot be imported'.format(module))
        return _fn
