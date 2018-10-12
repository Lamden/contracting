import redis, ast, marshal, array, copy, inspect
from seneca.constants.whitelists import allowed_ast_types, allowed_import_paths, safe_builtins

class SenecaInterpreter:

    r = redis.StrictRedis(host='localhost', port=6379, db=0)

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
    def assert_import_path(cls, import_path):
        for path in allowed_import_paths:
            if import_path.startswith(path):
                return True
        raise ImportError('Forbiddened to import module "{}"'.format(import_path))

    @classmethod
    def parse_ast(cls, code_str):
        tree = ast.parse(code_str)
        for item in ast.walk(tree):

            # Restrict imports to ones in allowed_import_paths
            if isinstance(item, ast.Import):
                cls.assert_import_path(item.names[0].name)
                print(item.names[0].name)
            elif isinstance(item, ast.ImportFrom):
                cls.assert_import_path(item.module)

        current_ast_types = {type(x) for x in ast.walk(tree)}
        illegal_ast_nodes = current_ast_types - allowed_ast_types
        assert not illegal_ast_nodes, 'Illegal AST node(s) in module: {}'.format(
            ', '.join(map(str, illegal_ast_nodes)))

        return tree

    @classmethod
    def execute(cls, code, scope={}):
        scope.update({
            '__builtins__': safe_builtins,
            'protected': Protected()
        })
        exec(code, scope)

class Protected:
    def __call__(self, fn, *args, **kwargs):
        def _fn():
            module = inspect.stack()[1].filename.replace('.sen.py', '').split('/')
            if len(module) >= 3:
                if module[-3] == fn.__module__.split('.')[-3]:
                    return fn(*args, **kwargs)
            raise Exception('Function "{}" is protected'.format(fn.__name__))
        return _fn
