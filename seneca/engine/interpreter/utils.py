from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SENECA_LIBRARY_PATH, ALLOWED_DATA_TYPES
import ast
from functools import lru_cache


class Plugins:

    __submit_stamps__ = None

    @staticmethod
    def assert_stamps(code_str):
        return '''
assert_stamps(__stamps__)
    ''' + code_str

    @classmethod
    def submit_stamps(cls):
        if not cls.__submit_stamps__:
            cls.__submit_stamps__ = compile('''
__stamps_used__ = __tracer__.get_stamp_used()
submit_stamps()
        ''', 'currency', 'exec')
        return cls.__submit_stamps__

    @staticmethod
    def import_module(code_str, module, func):
        return code_str + '''
__set_resources__()
__result__ = {func}()
'''.format(func=func)

    @staticmethod
    def resource_reassignment(varname, ctx):
        node = ast.parse('''
{}.resource_obj
        '''.format(varname), mode='exec').body[0].value
        node.ctx = ctx
        return node

    @staticmethod
    def global_reassignment(resource_list):
        return ast.parse('''
global {variables}
        '''.format(
            variables=','.join(resource_list)
        ))


class ReadOnlyException(Exception):
    pass


class CompilationException(Exception):
    pass


class NotImplementedException(Exception):
    pass


class ItemNotFoundException(Exception):
    pass


class Assert:

    @staticmethod
    def ast_types(t):
        if type(t) not in ALLOWED_AST_TYPES:
            raise CompilationException('Illegal AST type: {}'.format(t))

    @staticmethod
    def not_system_variable(v):
        if v.startswith('__') and v.endswith('__'):
            raise CompilationException('Access denied for system variable: {}'.format(v))

    @staticmethod
    def valid_import_path(import_path, module_name=None):
        if module_name == '*':
            raise ImportError('Not allowed to import *')
        elif module_name:
            import_path = '.'.join([import_path, module_name])
        if import_path.startswith(SENECA_LIBRARY_PATH):
            return 'lib_module'
        for path in ALLOWED_IMPORT_PATHS:
            if import_path.startswith(path):
                path_parts = import_path.split('.')
                if len(path_parts) - len(path.split('.')) == 2:
                    return 'smart_contract'
                else:
                    raise ImportError(
                        'Instead of importing the entire "{}" module, you must import each functions directly.'.format(
                            import_path))
        raise ImportError('Cannot find module "{}" in allowed protected_imports'.format(import_path))

    @staticmethod
    def is_protected(target, scope):
        if type(target) == ast.Name:
            contract_name = scope['rt']['contract']
            # print(contract_name, target.id, scope['protected']['__global__'])
            # print(scope['imports'])
            # print(scope['protected'])
            if target.id in scope['protected']['__global__'] \
                    or (scope['imports'].get(target.id) and contract_name not in scope['imports'].get(target.id, {})):
                raise ReadOnlyException('Cannot assign value to "{}" as it is a read-only variable'.format(target.id))

    @staticmethod
    def is_within_scope(target, protected, resources, scope):
        contract_name = scope['rt']['contract']
        if (scope.get(target) is not None and target not in protected and target not in resources \
                and target not in scope['protected']['__global__'] and contract_name not in scope['exports'].get(target, {})):
            if scope.get(target) and contract_name not in scope['exports'].get(target, {}):
                return
            # print(contract_name, target)
            # print(protected)
            # print(resources)
            # print(scope['protected']['__global__'])
            # print(scope['exports'])
            raise CompilationException('Not allowed to access "{}"'.format(target))

    @staticmethod
    def is_not_resource(assigned_to, name, scope):
        contract_name = scope['rt']['contract']
        resource = scope.get('resources', {}).get(contract_name, {}).get(assigned_to)
        if resource is False:
            raise ReadOnlyException('Cannot modify resource "{}.{}"'.format(contract_name, assigned_to))

    @staticmethod
    def no_nested_imports(node):
        for item in node.body:
            if type(item) in [ast.ImportFrom, ast.Import]:
                raise CompilationException('Not allowed to import inside a function definition')

    @staticmethod
    def is_datatype(node):
        if type(node.func) == ast.Name:
            if node.func.id not in ALLOWED_DATA_TYPES:
                raise CompilationException('Not allowed to call non-datatype objects in the global scope')

    @staticmethod
    def not_datatype(node):
        if type(node.func) == ast.Name:
            if node.func.id in ALLOWED_DATA_TYPES:
                raise CompilationException('Not allowed to instantiate DataTypes inside functions')

    @staticmethod
    def valid_assign(node, scope):
        for t in node.targets:
            Assert.is_protected(t, scope)

        invalid_assign = True
        assert len(node.targets) == 1, 'Short-hand multi assignment is not allowed'

        if type(node.targets[0]) == ast.Subscript:
            resource_name = node.targets[0].value.id
        elif type(node.targets[0]) == ast.Name:
            resource_name = node.targets[0].id

        if type(node.value) == ast.Call:
            if type(node.value.func) == ast.Name:
                func_name = node.value.func.id
                if func_name in ALLOWED_DATA_TYPES:
                    return resource_name, func_name

        if invalid_assign and not scope['ast']:
            raise CompilationException('You may only declare DataTypes or import modules in the global scope'
                                        ', line {}:{}, in {}'.format(node.lineno, node.col_offset, scope['rt']['contract']))

        return resource_name, None

    @staticmethod
    def validate(imports, exports, resources):
        # print(imports)
        # print(exports)
        # print(resources)
        for module, contracts in imports.items():
            for contract_name in contracts:
                if contract_name not in exports.get(module, {}) and module not in resources.get(contract_name, {}):
                    raise ImportError('Forbidden to import "{}.{}"'.format(
                        contract_name, module))