import redis, ast, marshal, array, copy, inspect, types, uuid
from seneca.constants.whitelists import allowed_ast_types, allowed_import_paths, safe_builtins

#0. will imports wrap into class methods or these wrappers with a default client (db=0) which redis-client can pass in active_db
#1. how do we wrap these redis commands in a such a way that they will execute against active_db
   #also reads if any have to use master_db
   #also a mode where extra meta data will be added or not?
#2. Directory structure / code organization
#3. do we need redis_client or can be merged into seneca_client itself

class SenecaInterpreter:

    def __init__(self, loop=None, name=None, get_log_fn=None, concurrent_mode=True):
        self.loop = loop or asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        name = name or self.__class__.__name__
        get_log_fn = get_log_fn or SenecaLogger
        self.log = get_log_fn(name)
        self.concurrent_mode = concurrent_mode
        # use dbs for copies  # todo - explore for namespaces also
        # change / pass port number
        port = 6379
        self.master_db = redis.StrictRedis(host='localhost', port=port, db=0)
        self.worker_dbs = []
        self.pending_dbs = []
        self.active_db = None  # pull the first one from worker_dbs when ready
        # add couple of worker dbs - can be done in a loop for max_number_workers
        self.max_number_workers = 2    # 2 sufficient for now
        # different clients have to be opened up front (as redis-py doesn't support select)
        for db_num in range(self.max_number_workers):
            db_client = redis.StrictRedis(host='localhost', port=port, db=db_num+1)
            self.worker_dbs.append(db_client)
      
        # connect to server here # persist  # ? use password - hashing of vk + sb_index ?


    # will be called upon the receipt of new-block-notification
    def flush(self, input/result_hash, update_state=True):
        """
        If update_state is True, this will also commit the changes
        to the database. Otherwise, this method will discard any changes
        """
        
        # need to iterate cur_db items and push them to master_db  - same as commit
        # make sure f_db is the one 
        f_db = self.pending_dbs.pop(0)    # actually it has to match result_hash
        if update_state:
            self.update_master_db(f_db)
        f_db.flushdb()
        self.worker_dbs.append(f_db)
        # pop the right one (should be first one mostly) from active_dbs
        # save the state to master_db and purge it completely and return it to worker_dbs

    def _start_next_db(self):
        if len(self.worker_dbs) == 0:
            return False
        self.active_db = self.worker_dbs.pop(0)
        # initialize it - add couple of special k-vs
        # input-bag hash ? or result-hash at the end so save can check the right one
        # sync counter ??
        # return true / false so higher level can throttle it the way it want
        # phases: 1 - execute contracts, 2 - assertion check / status
        return True


    def db_read(self, key):
        pass

    def db_write(self, key, value):
        pass

    def db_assert(self, key, assert_code):
        pass

    @classmethod
    def execute(cls, code, scope={}):
        scope.update({
            '__builtins__': safe_builtins,
            '__protected__': Protected(),
            'export': Export()
        })
        exec(code, scope)


    # raghu - can't be class variable without locks as many processes will try to update it simultaneously
    # perhaps in redis itself?
    imports = {}


    # raghu todo make them instance methods (not class methods)
    @classmethod
    def get_code_obj(cls, fullname):
        code_obj = cls.r.hget('contracts', fullname)
        assert code_obj, 'User module "{}" not found!'.format(fullname)
        return marshal.loads(code_obj)

    @classmethod
    def get_code_str(cls, fullname):
        code_str = cls.r.hget('contracts_str', fullname)
        assert code_str, 'Cannot find original code string for module "{}" not found!'.format(fullname)
        return code_str

    @classmethod
    def set_code(cls, fullname, code_str, keep_original=False):
        assert not cls.r.hexists('contracts', fullname), 'Contract "{}" already exists!'.format(fullname)
        tree = cls.parse_ast(code_str)
        code_obj = compile(tree, filename='module_name', mode="exec")
        pipe = cls.r.pipeline()
        pipe.hset('contracts', fullname, marshal.dumps(code_obj))
        if keep_original:
            pipe.hset('contracts_str', fullname, code_str)
        pipe.execute()

    @classmethod
    def assert_import_path(cls, import_path, module_name=None):
        if module_name:
            import_path = '.'.join([import_path, module_name])
        for path in allowed_import_paths:
            if import_path.startswith(path):
                if len(import_path.split('.')) - len(path.split('.')) == 2:
                    return True
                else:
                    raise ImportError('Instead of importing the entire "{}" module, you must import each functions directly.'.format(import_path))
        raise ImportError('"{}" is protected and cannot be imported'.format(import_path))

    @classmethod
    def parse_ast(cls, code_str, filename=''):

        tree = ast.parse(code_str)

        for idx, item in enumerate(ast.walk(tree)):

            # Restrict imports to ones in allowed_import_paths
            if isinstance(item, ast.Import):
                module_name = item.names[0].name
                cls.assert_import_path(module_name)
                if cls.imports.get(module_name) == 'protected':
                    raise ImportError('"{}" is protected and cannot be imported'.format(module_name))
                # raghu - falcon, why do we need this?
                cls.imports[module_name] = 'imported'

            elif isinstance(item, ast.ImportFrom):
                module_name = item.names[0].name
                cls.assert_import_path(item.module, module_name=module_name)
                imported = '.'.join([item.module, module_name])
                if cls.imports.get(imported) == 'protected':
                    raise ImportError('"{}" is protected and cannot be imported'.format(imported))
                # raghu - falcon, why do we need this?
                cls.imports[imported] = 'imported'

            # Add the __protected__ decorator if not export
            elif isinstance(item, ast.FunctionDef):
                decorators = [d.id for d in item.decorator_list]
                if '__protected__' in decorators:
                    raise ImportError('"{}" is protected and cannot be imported'.format(item.name))
                elif 'export' not in decorators:
                    node = ast.Name()
                    node.id = '__protected__'
                    node.ctx = ast.Load()
                    node.lineno = item.lineno
                    node.col_offset = 0
                    item.decorator_list.append(node)

        current_ast_types = {type(x) for x in ast.walk(tree)}
        illegal_ast_nodes = current_ast_types - allowed_ast_types
        assert not illegal_ast_nodes, 'Illegal AST node(s) in module: {}'.format(
            ', '.join(map(str, illegal_ast_nodes)))

        return tree

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
        SenecaInterpreter.imports[module] = 'protected'
        def _fn():
            if self.namespace in fn.__module__.split('.')[-1]:
                return fn(*args, **kwargs)
            raise ImportError('"{}" is __protected__ and cannot be imported'.format(module))
        return _fn
