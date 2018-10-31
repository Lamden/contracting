import redis, ast, marshal, inspect, sys
from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SAFE_BUILTINS, SENECA_LIBRARY_PATH
from seneca.constants.redis_config import get_redis_port, get_redis_password, MASTER_DB, DB_OFFSET
from seneca.engine.book_keeper import BookKeeper
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
    concurrent_mode = False

    @classmethod
    def setup(cls, concurrent_mode=True):
        cls.r = redis.StrictRedis(host='localhost', port=get_redis_port(), db=MASTER_DB, password=get_redis_password())
        from seneca.engine.module import SenecaFinder, RedisFinder
        cls.old_meta_path = sys.meta_path
        sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]
        cls.concurrent_mode = concurrent_mode
        cls._is_setup = True

    @classmethod
    def teardown(cls):
        sys.meta_path = cls.old_meta_path
        cls.concurrent_mode = False
        cls._is_setup = False

    @classmethod
    def execute_contract(cls, code_str: str, sender: str, sbb_idx: int, contract_idx: int, master_db: redis.StrictRedis,
                         working_db: redis.StrictRedis, author=''):
        assert cls._is_setup, "SenecaInterpreter.setup() must be called before you can execute_contract"

        author = author or 'claude shannon'  # For now, we mock the author
        rt_info = {'rt': make_n_tup({'sender': sender, 'author': author})}

        BookKeeper.set_info(sbb_idx=sbb_idx, contract_idx=contract_idx, master_db=master_db, working_db=working_db)

        tree = SenecaInterpreter.parse_ast(code_str, protected_variables=list(rt_info.keys()))
        code_obj = compile(tree, filename='__main__', mode="exec")
        SenecaInterpreter.execute(code_obj, scope=rt_info)

        BookKeeper.del_info()  # TODO is this necessary? It will just get overriden on next set_info(). --davis


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
    def set_code(cls, fullname, code_str, keep_original=False, scope={}):
        assert not cls.r.hexists('contracts', fullname), 'Contract "{}" already exists!'.format(fullname)
        tree = cls.parse_ast(code_str)
        code_obj = compile(tree, filename='module_name', mode="exec")
        cls.execute(code_obj, scope)
        cls.validate()
        pipe = cls.r.pipeline()
        pipe.hset('contracts', fullname, marshal.dumps(code_obj))
        if keep_original:
            pipe.hset('contracts_str', fullname, code_str)
        pipe.execute()

    @classmethod
    def remove_code(cls, fullname):
        pipe = cls.r.pipeline()
        pipe.hdel('contracts', fullname)
        pipe.hdel('contracts_str', fullname)
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
                raise CompilationException('Forbidden to import the following: {}'.format(
                    cls.imports))

    @classmethod
    def parse_ast(cls, code_str, protected_variables=[]):

        tree = ast.parse(code_str)
        protected_variables += ['export']
        current_ast_types = set()

        for idx, item in enumerate(ast.walk(tree)):

            # Restrict protected_imports to ones in ALLOWED_IMPORT_PATHS
            if isinstance(item, ast.Import):
                module_name = item.names[0].name
                cls.assert_import_path(module_name)

            elif isinstance(item, ast.ImportFrom):
                module_name = item.names[0].name
                cls.assert_import_path(item.module, module_name=module_name)

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

            current_ast_types.add(type(item))

        illegal_ast_nodes = current_ast_types - ALLOWED_AST_TYPES
        assert not illegal_ast_nodes, 'Illegal AST node(s) in module: {}'.format(
            ', '.join(map(str, illegal_ast_nodes)))

        return tree

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


class ScopeParser:
    @property
    def namespace(self):
        return inspect.stack()[2].filename.replace('.sen.py', '').split('/')[-1]

    def set_scope(self, fn):
        fn.__globals__.update(SenecaInterpreter.loaded['__main__'])

    def set_scope_during_compilation(self, fn):
        self.module = '.'.join([fn.__module__ or '', fn.__name__])
        fn.__globals__['__contract__'] = fn.__module__

class Export(ScopeParser):

    def __call__(self, fn):
        self.set_scope_during_compilation(fn)
        SenecaInterpreter.exports[self.module] = True
        def _fn(*args, **kwargs):
            self.set_scope(fn)
            return fn(*args, **kwargs)
        return _fn

