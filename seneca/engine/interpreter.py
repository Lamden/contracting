import redis, ast, marshal, array, copy, inspect, types, uuid, copy, ujson as json, sys, time
from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SAFE_BUILTINS, SENECA_LIBRARY_PATH
from seneca.constants.config import get_redis_port, get_redis_password, MASTER_DB, DB_OFFSET, CODE_OBJ_MAX_CACHE
from functools import lru_cache
from tracer import Tracer
import seneca, os
from os.path import join

class ReadOnlyException(Exception):
    pass

class CompilationException(Exception):
    pass

class SenecaInterpreter:

    exports = {}
    imports = {}
    loaded = {}
    cache = {}
    _is_setup = False
    concurrent_mode = True

    @classmethod
    def setup(cls, concurrent_mode=True):
        if not cls._is_setup:
            cls.r = redis.StrictRedis(host='localhost', port=get_redis_port(), db=MASTER_DB, password=get_redis_password())
            cls._is_setup = True
            cls.setup_tracer()
        cls.concurrent_mode = concurrent_mode

    @classmethod
    def setup_tracer(cls):
        seneca_path = seneca.__path__[0]
        path = join(seneca_path, 'constants', 'cu_costs.const')
        os.environ['CU_COST_FNAME'] = path
        cls.tracer = Tracer()

    @classmethod
    def teardown(cls):
        cls._is_setup = False

    @classmethod
    def get_code_obj(cls, fullname):
        assert cls._is_setup, "Must be set up to get_code_obj!!!!"
        code_obj = cls.r.hget('contracts', fullname)
        assert code_obj, 'User module "{}" not found!'.format(fullname)
        return marshal.loads(code_obj)

    @classmethod
    def get_code_str(cls, fullname):
        meta = cls.get_contract_meta(fullname)
        assert meta.get('code_str'), 'Cannot find original code string for module "{}" not found!'.format(fullname)
        return meta['code_str']

    @classmethod
    def get_contract_meta(cls, fullname):
        byte_str = cls.r.hget('contracts_meta', fullname)
        assert byte_str, 'Contract "{}" does not exist.'.format(fullname)
        meta = json.loads(byte_str)
        return meta

    @classmethod
    def set_code(cls, fullname, code_obj, code_str, author, keep_original=False):
        pipe = cls.r.pipeline()
        pipe.hset('contracts', fullname, marshal.dumps(code_obj))
        pipe.hset('contracts_meta', fullname, json.dumps({
            'code_str': code_str,
            'author': author,
            'timestamp': time.time()
        }))
        pipe.execute()

    @classmethod
    def remove_code(cls, fullname):
        pipe = cls.r.pipeline()
        pipe.hdel('contracts', fullname)
        pipe.hdel('contracts_meta', fullname)
        pipe.execute()

    @classmethod
    def code_obj_exists(cls, fullname) -> bool:
        return bool(cls.r.hget('contracts', fullname))

    @classmethod
    def assert_import_path(cls, import_path, module_name=None):
        if module_name == '*':
            raise ImportError('Not allowed to import *')
        elif module_name:
            import_path = '.'.join([import_path, module_name])
        if import_path.startswith(SENECA_LIBRARY_PATH):
            cls.exports[import_path] = True
            return True
        for path in ALLOWED_IMPORT_PATHS:
            if import_path.startswith(path):
                if len(import_path.split('.')) - len(path.split('.')) == 2:
                    if not cls.exports.get(import_path):
                        cls.imports[import_path] = True
                    return True
                else:
                    raise ImportError('Instead of importing the entire "{}" module, you must import each functions directly.'.format(import_path))
        raise ImportError('Cannot find module "{}" in allowed protected_imports'.format(import_path))

    @classmethod
    def validate(cls):
        for import_path in cls.imports:
            if not cls.exports.get(import_path):
                raise CompilationException('Forbidden to import "{}"'.format(
                    import_path))

    @classmethod
    def parse_ast(cls, code_str, protected_variables=[]):

        tree = ast.parse(code_str)
        protected_variables += ['export']
        current_ast_types = set()
        prevalidated = copy.deepcopy(tree)
        prevalidated.body = []

        for idx, item in enumerate(ast.walk(tree)):

            if isinstance(item, ast.Name):
                if cls.is_system_variable(item.id):
                    raise CompilationException('Not allowed to read "{}"'.format(item.id))

            # Restrict __attr__ to be accessed
            if isinstance(item, ast.Attribute):
                if cls.is_system_variable(item.attr):
                    raise CompilationException('Not allowed to read "{}"'.format(item.attr))

            # Restrict protected_imports to ones in ALLOWED_IMPORT_PATHS
            elif isinstance(item, ast.Import):
                module_name = item.names[0].name
                cls.assert_import_path(module_name)
                prevalidated.body.append(item)

            elif isinstance(item, ast.ImportFrom):
                module_name = item.names[0].name
                cls.assert_import_path(item.module, module_name=module_name)
                prevalidated.body.append(item)

            # Restrict variable assignment
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    cls.check_protected(target, protected_variables)

            elif isinstance(item, ast.AugAssign):
                cls.check_protected(item.target, protected_variables)

            elif isinstance(item, ast.FunctionDef):
                for fn_item in item.body:
                    if isinstance(fn_item, (ast.Import, ast.ImportFrom)):
                        raise ImportError('Cannot import modules inside a function!')

                prevalidated.body.append(item)
            current_ast_types.add(type(item))

        illegal_ast_nodes = current_ast_types - ALLOWED_AST_TYPES
        assert not illegal_ast_nodes, 'Illegal AST node(s) in module: {}'.format(
            ', '.join(map(str, illegal_ast_nodes)))

        return tree, prevalidated

    @staticmethod
    def is_system_variable(v):
        return v.startswith('__') and v.endswith('__')

    @classmethod
    def check_protected(cls, target, protected_variables):
        if isinstance(target, ast.Subscript):
            return
        if target.id in protected_variables \
            or target.id in [k.rsplit('.', 1)[-1] for k in cls.imports.keys()]:
            raise ReadOnlyException('Cannot assign value to "{}" as it is a read-only variable'.format(target.id))

    @classmethod
    def execute(cls, code, scope={}, is_main=True):
        scope.update({
            'export': Export(),
            '__builtins__': SAFE_BUILTINS,
            '__use_locals__': False,
        })
        if is_main:
            cls.loaded['__main__'] = scope
        exec(code, scope)
        if is_main:
            cls.validate()

    @classmethod
    @lru_cache(maxsize=CODE_OBJ_MAX_CACHE)
    def get_cached_code_obj(cls, module_path):
        cls.assert_import_path(module_path)
        module = module_path.rsplit('.', 1)
        code_str = '''
result = {}()
        '''.format(module[1])
        code_obj = compile(code_str, '__main__', 'exec')
        import_obj = compile('from {} import {}'.format(module[0], module[1]), '__main__', 'exec')
        return code_obj, import_obj

    @classmethod
    def execute_function(cls, module_path, author, sender, stamps, *args, **kwargs):
        scope = {
            'rt': { 'author': author, 'sender': sender, 'contract': module_path },
            '__builtins__': SAFE_BUILTINS,
            '__args__': args,
            '__kwargs__': kwargs,
            '__use_locals__': True
        }
        code_obj, import_obj = cls.get_cached_code_obj(module_path)
        cls.loaded['__main__'] = scope
        exec(import_obj, scope)
        cls.tracer.set_stamp(stamps)
        cls.tracer.start()
        exec(code_obj, scope)
        cls.tracer.stop()
        # print('xxx',cls.tracer.get_stamp_used())
        return {
            'status': 'success',
            'output': scope.get('result'),
            'remaining_stamps': stamps - cls.tracer.get_stamp_used()
        }

class ScopeParser:

    def set_scope(self, fn, args, kwargs):
        fn.__globals__.update(SenecaInterpreter.loaded['__main__'])
        fn.__globals__['rt']['contract'] = fn.__module__
        if fn.__globals__.get('__use_locals__'):
            if fn.__globals__.get('__args__'): args = fn.__globals__['__args__']
            if fn.__globals__.get('__kwargs__'): kwargs = fn.__globals__['__kwargs__']
        return args, kwargs

    def set_scope_during_compilation(self, fn):
        self.module = '.'.join([fn.__module__, fn.__name__])
        SenecaInterpreter.exports[self.module] = True

class Export(ScopeParser):
    def __call__(self, fn):
        if not fn.__module__: return
        self.set_scope_during_compilation(fn)
        def _fn(*args, **kwargs):
            args, kwargs = self.set_scope(fn, args, kwargs)
            return fn(*args, **kwargs)
        return _fn
