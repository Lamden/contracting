import redis, ast, marshal, array, copy, inspect, types, uuid, copy, ujson as json, sys, time
from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SAFE_BUILTINS, SENECA_LIBRARY_PATH
from seneca.constants.redis_config import get_redis_port, get_redis_password, MASTER_DB, DB_OFFSET
from seneca.libs.logger import get_logger
from seneca.engine.util import make_n_tup


class ReadOnlyException(Exception):
    pass


class CompilationException(Exception):
    pass


class SenecaInterpreter:

    exports = {}
    imports = {}
    loaded = {}
    _is_setup = False
    concurrent_mode = True

    @classmethod
    def setup(cls, concurrent_mode=True):
        if not cls._is_setup:
            cls.r = redis.StrictRedis(host='localhost', port=get_redis_port(), db=MASTER_DB, password=get_redis_password())
            cls._is_setup = True
            cls.concurrent_mode = concurrent_mode

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
            # print(cls.exports)
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

            # Restrict protected_imports to ones in ALLOWED_IMPORT_PATHS
            if isinstance(item, ast.Import):
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
                # for dec in item.decorator_list:
                #     if dec.id == 'export':
                #         print(dir(item))
                #         print(item.name)
                #         print(item.args.args)
                #         break

                prevalidated.body.append(item)

            current_ast_types.add(type(item))

        illegal_ast_nodes = current_ast_types - ALLOWED_AST_TYPES
        assert not illegal_ast_nodes, 'Illegal AST node(s) in module: {}'.format(
            ', '.join(map(str, illegal_ast_nodes)))

        return tree, prevalidated

    @staticmethod
    def check_protected(target, protected_variables):
        if isinstance(target, ast.Subscript):
            return
        if target.id.startswith('__') and target.id.endswith('__') \
            or target.id in protected_variables:
            raise ReadOnlyException('Cannot assign value to "{}" as it is a read-only variable'.format(target.id))

    @classmethod
    def execute(cls, code, scope={}, is_main=True):
        scope.update({
            '__builtins__': SAFE_BUILTINS,
            'export': Export()
        })
        if is_main:
            cls.loaded['__main__'] = scope
        exec(code, scope)
        if is_main:
            cls.validate()

    @classmethod
    def execute_function(cls, module_path, author, sender, *args, **kwargs):
        cls.assert_import_path(module_path)
        module = module_path.rsplit('.', 1)
        code_str = '''
from {} import {}
result = {}({}, {})
        '''.format(module[0], module[1], module[1],
            ','.join([json.dumps(arg) for arg in args]),
            ','.join(['{}={}'.format(k,json.dumps(v)) for k,v in kwargs.items()])
        )
        scope = {'rt': make_n_tup({
            'author': author,
            'sender': sender
        })}
        cls.loaded['__main__'] = scope
        exec(code_str, scope)
        return scope.get('result')

class ScopeParser:
    @property
    def namespace(self):
        return inspect.stack()[2].filename.replace('.sen.py', '').split('/')[-1]

    def set_scope(self, fn):
        fn.__globals__.update(SenecaInterpreter.loaded['__main__'])

    def set_scope_during_compilation(self, fn):
        self.module = '.'.join([fn.__module__, fn.__name__])
        fn.__globals__['__contract__'] = fn.__module__

class Export(ScopeParser):
    def __call__(self, fn):
        if not fn.__module__:
            return
        self.set_scope_during_compilation(fn)
        SenecaInterpreter.exports[self.module] = True
        def _fn(*args, **kwargs):
            self.set_scope(fn)
            return fn(*args, **kwargs)
        return _fn
