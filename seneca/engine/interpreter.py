import redis, ast, marshal, array, copy, inspect, types, uuid
from seneca.constants.whitelists import allowed_ast_types, allowed_import_paths, safe_builtins

class SenecaInterpreter:

    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    imports = {}


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
                cls.imports[module_name] = 'imported'

            elif isinstance(item, ast.ImportFrom):
                module_name = item.names[0].name
                cls.assert_import_path(item.module, module_name=module_name)
                imported = '.'.join([item.module, module_name])
                if cls.imports.get(imported) == 'protected':
                    raise ImportError('"{}" is protected and cannot be imported'.format(imported))
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

    @classmethod
    def execute(cls, code, scope={}):
        scope.update({
            '__builtins__': safe_builtins,
            '__protected__': Protected(),
            'export': Export()
        })
        exec(code, scope)

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
