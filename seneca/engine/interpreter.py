import redis, ast, marshal, array, copy, inspect, types, uuid, copy
from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SAFE_BUILTINS

class ReadOnlyException(Exception):
    pass

class CompilationException(Exception):
    pass

class SenecaInterpreter:

    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    invalid_exports = {}
    loaded = {}

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
        cls.validate()
        SenecaInterpreter.execute(code_obj, {})
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

        for path in ALLOWED_IMPORT_PATHS:
            if import_path.startswith(path):
                if len(import_path.split('.')) - len(path.split('.')) == 2:
                    if not cls.invalid_exports.get(import_path):
                        cls.invalid_exports[import_path] = 'invalid'
                    return True
                else:
                    raise ImportError('Instead of importing the entire "{}" module, you must import each functions directly.'.format(import_path))
        raise ImportError('Cannot find module "{}" in allowed protected_imports'.format(import_path))

    @classmethod
    def validate(cls):
        invalid_exports = [k for k, v in cls.invalid_exports.items() if v != 'exported']
        cls.invalid_exports = {}
        if len(cls.invalid_exports) > 0:
            raise CompilationException('Forbidden to import the following: {}'.format(
                invalid_exports))

    @classmethod
    def parse_ast(cls, code_str, protected_variables=[]):

        tree = ast.parse(code_str)
        protected_variables += ['export']
        current_ast_types = set()

        for idx, item in enumerate(ast.walk(tree)):

            # # Restrict top level code to function definitions and imports
            # if isinstance(item, ast.Module):
            #     # print(vars(item))
            #     for module_item in item.body:
            #         if isinstance(module_item, ast.Assign):
            #             for target in module_item.targets:
            #                 pass
            #                 # print(cls.protected_imports)

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

            # Add the __protected__ decorator if not export
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
        if SenecaInterpreter.invalid_exports.get(self.module) == 'imported':
            del SenecaInterpreter.invalid_exports[self.module]
        else:
            SenecaInterpreter.invalid_exports[self.module] = 'exported'
        def _fn(*args, **kwargs):
            self.set_scope(fn)
            return fn(*args, **kwargs)
        return _fn
