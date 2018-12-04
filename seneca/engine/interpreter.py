import redis, ast, marshal, array, copy, inspect, types, uuid, copy, ujson as json, sys, time
from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SAFE_BUILTINS, SENECA_LIBRARY_PATH
from seneca.constants.config import get_redis_port, get_redis_password, MASTER_DB, DB_OFFSET, CODE_OBJ_MAX_CACHE
from functools import lru_cache
from seneca.libs.metering.tracer import Tracer
import seneca, os
from os.path import join
from seneca.engine.book_keeper import BookKeeper

class ReadOnlyException(Exception):
    pass


class CompilationException(Exception):
    pass


class Seneca:
    current_ast_types = None
    prevalidated = None
    postvalidated = None
    protected_variables = None
    concurrent_mode = True
    interface = None

    exports = {}
    imports = {}
    loaded = {}
    cache = {}

    basic_scope = {}


class ScopeParser:
    def set_scope(self, fn, args, kwargs):
        fn.__globals__.update(Seneca.loaded['__main__'])
        fn.__globals__['rt']['contract'] = fn.__module__
        if fn.__globals__.get('__use_locals__'):
            if fn.__globals__.get('__args__'): args = fn.__globals__['__args__']
            if fn.__globals__.get('__kwargs__'): kwargs = fn.__globals__['__kwargs__']
        return args, kwargs

    def set_scope_during_compilation(self, fn):
        self.module = '.'.join([fn.__module__, fn.__name__])
        Seneca.exports[self.module] = True


class Export(ScopeParser):
    def __call__(self, fn):
        if not fn.__module__: return
        self.set_scope_during_compilation(fn)

        def _fn(*args, **kwargs):
            args, kwargs = self.set_scope(fn, args, kwargs)
            return fn(*args, **kwargs)
        return _fn


class Seed(ScopeParser):
    def __call__(self, fn):
        if fn.__globals__.get('__seed__') == True:
            old_concurrent_mode = Seneca.concurrent_mode
            Seneca.concurrent_mode = False
            fn()
            Seneca.concurrent_mode = old_concurrent_mode


Seneca.basic_scope = {
    'export': Export(),
    'seed': Seed(),
    '__builtins__': SAFE_BUILTINS,
    '__use_locals__': False
}


class SenecaNodeTransformer(ast.NodeTransformer):
    def generic_visit(self, node):
        Seneca.current_ast_types.add(type(node))
        return super().generic_visit(node)

    def visit_Name(self, node):
        if SenecaInterpreter.is_system_variable(node.id):
            raise CompilationException('Not allowed to read "{}"'.format(node.id))
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        if SenecaInterpreter.is_system_variable(node.attr):
            raise CompilationException('Not allowed to read "{}"'.format(node.attr))
        self.generic_visit(node)
        return node

    def visit_Import(self, node):
        module_name = node.names[0].name
        SenecaInterpreter.assert_import_path(module_name)
        Seneca.prevalidated.body.append(node)
        self.generic_visit(node)
        Seneca.postvalidated.body.append(node)
        return node

    def visit_ImportFrom(self, node):
        module_name = node.names[0].name
        SenecaInterpreter.assert_import_path(node.module, module_name=module_name)
        Seneca.prevalidated.body.append(node)
        self.generic_visit(node)
        Seneca.postvalidated.body.append(node)
        return node

    def visit_Assign(self, node):
        for target in node.targets:
            SenecaInterpreter.check_protected(target, Seneca.protected_variables)
        if type(node.value) == ast.Call:
            Seneca.postvalidated.body.append(node)
        self.generic_visit(node)
        return node

    def visit_AugAssign(self, node):
        SenecaInterpreter.check_protected(node.target, Seneca.protected_variables)
        self.generic_visit(node)
        return node

    def visit_Num(self, node):
        if isinstance(node.n, float) or isinstance(node.n, int):
            return ast.Call(func=ast.Name(id='make_decimal', ctx=ast.Load()),
                            args=[node], keywords=[])
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        for item in node.body:
            if type(item) in [ast.ImportFrom, ast.Import]:
                raise CompilationException('Not allowed to import inside a function definition')
        for item in node.decorator_list:
            if item.id == 'export':
                Seneca.exports[node.name] = True
        return node


class SenecaInterpreter:
    def __init__(self, concurrent_mode=True, port=None, password=None):
        self.r = redis.StrictRedis(host='localhost',
                                  port=get_redis_port(port=port),
                                  db=MASTER_DB,
                                  password=get_redis_password(password=password)
                                  )
        self.setup_tracer()
        Seneca.concurrent_mode = concurrent_mode

    def setup_tracer(self):
        seneca_path = seneca.__path__[0]
        path = join(seneca_path, 'constants', 'cu_costs.const')
        os.environ['CU_COST_FNAME'] = path
        self.tracer = Tracer()

    def get_code_obj(self, fullname):
        code_obj = self.r.hget('contracts', fullname)
        assert code_obj, 'User module "{}" not found!'.format(fullname)
        return marshal.loads(code_obj)

    def get_code_str(self, fullname):
        meta = self.get_contract_meta(fullname)
        assert meta.get('code_str'), 'Cannot find original code string for module "{}" not found!'.format(fullname)
        return meta['code_str']

    def get_contract_meta(self, fullname):
        byte_str = self.r.hget('contracts_meta', fullname)
        meta = json.loads(byte_str)
        return meta

    def set_code(self, fullname, tree_obj, code_obj, code_str, author):
        pipe = self.r.pipeline()
        pipe.hset('contracts', fullname, marshal.dumps(tree_obj))
        pipe.hset('contracts_code', fullname, marshal.dumps(code_obj))
        pipe.hset('contracts_meta', fullname, json.dumps({
            'code_str': code_str,
            'author': author,
            'timestamp': time.time()
        }))
        pipe.execute()

    def remove_code(self, fullname):
        pipe = self.r.pipeline()
        pipe.hdel('contracts', fullname)
        pipe.hdel('contracts_code', fullname)
        pipe.hdel('contracts_meta', fullname)
        pipe.execute()

    @staticmethod
    def parse_ast(code_str, protected_variables=[]):

        # crude but effective way to force fixed precision without developer behavior change
        decimal_addon = 'from seneca.libs.decimal import make_decimal'

        code_str = decimal_addon + '\n' + code_str

        Seneca.current_ast_types = set()
        Seneca.protected_variables = protected_variables

        tree = ast.parse(code_str)
        Seneca.protected_variables += ['export']
        Seneca.prevalidated = copy.deepcopy(tree)
        Seneca.prevalidated.body = []
        Seneca.postvalidated = copy.deepcopy(tree)
        Seneca.postvalidated.body = []

        tree = SenecaNodeTransformer().visit(tree)
        ast.fix_missing_locations(tree)

        illegal_ast_nodes = Seneca.current_ast_types - ALLOWED_AST_TYPES
        assert not illegal_ast_nodes, 'Illegal AST node(s) in module: {}'.format(
            ', '.join(map(str, illegal_ast_nodes)))

        return tree, Seneca.postvalidated, Seneca.prevalidated

    @staticmethod
    def validate():
        for import_path in Seneca.imports:
            if not Seneca.exports.get(import_path):
                raise CompilationException('Forbidden to import "{}"'.format(
                    import_path))

    @staticmethod
    def is_system_variable(v):
        return v.startswith('__') and v.endswith('__')

    @staticmethod
    def check_protected(target, protected_variables):
        if isinstance(target, ast.Subscript):
            return
        if target.id in protected_variables \
            or target.id in [k.rsplit('.', 1)[-1] for k in Seneca.imports.keys()]:
            raise ReadOnlyException('Cannot assign value to "{}" as it is a read-only variable'.format(target.id))

    @staticmethod
    def assert_import_path(import_path, module_name=None):
        if module_name == '*':
            raise ImportError('Not allowed to import *')
        elif module_name:
            import_path = '.'.join([import_path, module_name])
        if import_path.startswith(SENECA_LIBRARY_PATH):
            Seneca.exports[import_path] = True
            return True
        for path in ALLOWED_IMPORT_PATHS:
            if import_path.startswith(path):
                if len(import_path.split('.')) - len(path.split('.')) == 2:
                    if not Seneca.exports.get(import_path):
                        Seneca.imports[import_path] = True
                    return True
                else:
                    raise ImportError('Instead of importing the entire "{}" module, you must import each functions directly.'.format(import_path))
        raise ImportError('Cannot find module "{}" in allowed protected_imports'.format(import_path))

    def execute(self, code, scope={}, is_main=True):
        scope.update(Seneca.basic_scope)
        if is_main:
            Seneca.loaded['__main__'] = scope
        Seneca.loaded['__main__'].update(scope)

        exec(code, scope)
        if is_main:
            self.validate()

    @lru_cache(maxsize=CODE_OBJ_MAX_CACHE)
    def get_cached_code_obj(self, module_path, stamps_supplied):
        self.assert_import_path(module_path)
        module = module_path.rsplit('.', 1)
        meta = self.get_contract_meta(module[0].rsplit('.')[-1])
        if stamps_supplied != None:
            import_obj = compile('''
from seneca.contracts.currency import submit_stamps
submit_stamps({})
from {} import {}
            '''.format(stamps_supplied, module[0], module[1]), '__main__', 'exec')
        else:
            import_obj = compile('''
from {} import {}
            '''.format(module[0], module[1]), '__main__', 'exec')
        code_str = '''
result = {}()
        '''.format(module[1])
        fn_call_obj = compile(code_str, '__main__', 'exec')
        # import_obj = marshal.loads(self.r.hget('contracts_code', module[0].rsplit('.', 1)[-1]))

        return fn_call_obj, import_obj, meta

    def execute_function(self, module_path, sender, stamps, *args, **kwargs):
        module_name = module_path.rsplit('.', 1)[0]
        contract_name = module_name.rsplit('.', 1)[-1]
        fn_call_obj, import_obj, meta = self.get_cached_code_obj(module_path, stamps)
        scope = {
            'rt': { 'author': meta['author'], 'sender': sender, 'contract': contract_name },
            '__args__': args,
            '__kwargs__': kwargs,
        }
        scope.update(Seneca.basic_scope)
        Seneca.loaded['__main__'] = scope
        print(scope)
        exec(import_obj, scope)
        _obj = marshal.loads(self.r.hget('contracts_code', contract_name))
        exec(_obj, scope)
        scope.update({'__use_locals__': True})
        if stamps != None:
            self.tracer.set_stamp(stamps)
            self.tracer.start()
            exec(fn_call_obj, scope)
            self.tracer.stop()
            stamps -= self.tracer.get_stamp_used()
        else:
            exec(fn_call_obj, scope)
            stamps = 0
        return {
            'status': 'success',
            'output': scope.get('result'),
            'remaining_stamps': stamps
        }
