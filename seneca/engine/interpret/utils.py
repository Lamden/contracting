from seneca.constants.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SENECA_LIBRARY_PATH, ALLOWED_DATA_TYPES
import ast

class Plugins:

    @staticmethod
    def stamps(code_str):
        return '''
submit_stamps()
''' + code_str

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
    def valid_import_path(import_path, module_name=None, contract_name=None):
        if module_name == '*':
            raise ImportError('Not allowed to import *')
        elif module_name:
            import_path = '.'.join([import_path, module_name])
        if import_path.startswith(SENECA_LIBRARY_PATH):
            return
        for path in ALLOWED_IMPORT_PATHS:
            if import_path.startswith(path):
                path_parts = import_path.split('.')
                if len(path_parts) - len(path.split('.')) == 2:
                    return path_parts[-1]
                else:
                    raise ImportError(
                        'Instead of importing the entire "{}" module, you must import each functions directly.'.format(
                            import_path))
        raise ImportError('Cannot find module "{}" in allowed protected_imports'.format(import_path))

    @staticmethod
    def is_protected(target, scope):
        if type(target) == ast.Name:
            if target.id in scope['protected']['global'].union(scope['protected'][scope['rt']['contract']]) \
                    or target.id in [k.rsplit('.', 1)[-1] for k in scope['imports'].keys()]:
                raise ReadOnlyException('Cannot assign value to "{}" as it is a read-only variable'.format(target.id))

    @staticmethod
    def is_not_resource(name, scope):
        if name in scope['resources']:
            raise ImportError('Cannot import "{}" as it is a resource variable'.format(name))

    @staticmethod
    def no_nested_imports(node):
        for item in node.body:
            if type(item) in [ast.ImportFrom, ast.Import]:
                raise CompilationException('Not allowed to import inside a function definition')

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
        if type(node.value) == ast.Call:
            assert len(node.targets) == 1, 'You can only declare one DataType at a time'
            resource_name = node.targets[0].id
            if type(node.value.func) == ast.Name:
                func_name = node.value.func.id
                if func_name in ALLOWED_DATA_TYPES:
                    return resource_name, func_name

        if invalid_assign and not scope['ast']:
            raise CompilationException('You may only declare DataTypes or import modules in the global scope'
                                        ', line {}:{}, in {}'.format(node.lineno, node.col_offset, scope['rt']['contract']))


        return None, None

    @staticmethod
    def validate(imports, exports):
        for import_path in imports:
            if not exports.get(import_path):
                raise ImportError('Forbidden to import "{}"'.format(
                    import_path))