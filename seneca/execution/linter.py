from seneca.execution.whitelists import ALLOWED_AST_TYPES, ALLOWED_IMPORT_PATHS, SENECA_LIBRARY_PATH
from seneca.logger import get_logger
import ast
from ast import Assert
from seneca.utils import CompilationException, ReadOnlyException
# from seneca.constants.config import *

class Linter(ast.NodeVisitor):
    def __init__(self):
        self.log = get_logger('Seneca.Parser')
        self._reset()

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
        contract_name = scope['rt']['contract']
        if scope.get('__system__'):
            return
        if type(target) == ast.Name:
            # print(target.id)
            # print('\t', scope['protected']['__global__'])
            # print('\t', scope['imports'])
            if target.id in scope['protected']['__global__'] \
                    or (scope['imports'].get(target.id) and contract_name not in scope['imports'].get(target.id, {})):
                raise ReadOnlyException('Cannot assign value to "{}" as it is a read-only variable'.format(target.id))

    @staticmethod
    def is_within_scope(target, protected, resources, scope):
        contract_name = scope['rt']['contract']

        if (scope.get(target) is not None and target not in protected and target not in resources
                and target not in scope['protected']['__global__'] and contract_name not in scope['exports'].get(target, {})):
            if scope.get(target) and contract_name not in scope['exports'].get(target, {}):
                return
            if not scope.get(target):
                return
            # print(contract_name, target)
            # print(protected)
            # print(resources)
            # print(scope['protected']['__global__'])
            # print(scope['exports'])
            raise CompilationException('Not allowed to access "{}"'.format(target))

    @staticmethod
    def is_not_resource(resource_names, name, scope):
        for assigned_to in resource_names:
            contract_name = scope['rt']['contract']
            resource = scope.get('resources', {}).get(contract_name, {}).get(assigned_to)
            if resource is False:
                raise ReadOnlyException('Cannot modify resource "{}.{}"'.format(contract_name, assigned_to))

    @staticmethod
    def no_nested_imports(node):
        for item in node.body:
            if type(item) in [ast.ImportFrom, ast.Import]:
                raise CompilationException('Not allowed to import inside a function definition')

    def is_datatype(self, node):
        if type(node.func) == ast.Name:
            if node.func.id not in ALLOWED_DATA_TYPES and node.func.id not in self._functions:
                self.log.error('{}: Not allowed to call non-datatype objects in the global scope'.format(node.func.id))
                self._is_success = False

    @staticmethod
    def not_datatype(node):
        if type(node.func) == ast.Name:
            if node.func.id in ALLOWED_DATA_TYPES:
                self.log.error('{}: Not allowed to instantiate DataTypes inside functions'.format(node.func.id))
                self._is_success = False

    @staticmethod
    def check_assignment_targets(node):
        resource_names = []
        if type(node) == ast.Assign:
            for n in node.targets:
                resource_names += Assert.check_assignment_targets(n)
        elif type(node) == ast.Name:
            resource_names.append(node.id)
        elif type(node) in (ast.Subscript, ast.Attribute):
            resource_names += Assert.check_assignment_targets(node.value)
        elif type(node) == ast.Tuple:
            for n in node.elts:
                resource_names += Assert.check_assignment_targets(n)
        return resource_names

    @staticmethod
    def valid_assign(node, scope):
        for t in node.targets:
            self.is_protected(t, scope)

        resource_names = Assert.check_assignment_targets(node)

        if type(node.value) == ast.Call:
            if type(node.value.func) == ast.Name:
                func_name = node.value.func.id
                if func_name in ALLOWED_DATA_TYPES:
                    return resource_names, func_name

        if not scope['ast']:
            raise CompilationException('You may only declare DataTypes or import modules in the global scope'
                                        ', line {}:{}, in {}'.format(node.lineno, node.col_offset, scope['rt']['contract']))

        return resource_names, None

    @staticmethod
    def validate(imports, exports, resources, current_contract):
        for module, contracts in imports.items():
            for contract_name in contracts:
                if contract_name not in exports.get(module, {}) and module not in resources.get(contract_name, {}):
                    # print(contract_name, module)
                    # print(imports)
                    # print(exports)
                    # print(resources)
                    raise ImportError('Forbidden to import "{}.{}"'.format(
                        contract_name, module))

    def generic_visit(self, node):
        self.ast_types(node)
        return super().generic_visit(node)

    def visit_Name(self, node):
        # self.is_protected(node, Parser.parser_scope)
        self.not_system_variable(node.id)
        # Assert.is_within_scope(node.id, self.protected, self.resource, Parser.parser_scope)
        # if Parser.assigning:
            # Assert.is_not_resource(Parser.assigning, node.id, Parser.parser_scope)
        # if Parser.parser_scope['ast'] in ('seed', 'export', 'func') \
                # and self.get_resource(node.id) == 'Resource':
            # self.generic_visit(node)
            # return Plugins.resource_reassignment(node.id, node.ctx)
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        self.not_system_variable(node.attr)
        self.generic_visit(node)
        return node

    def visit_Import(self, node):
        for n in node.names:
            self.validate_imports(n.name, alias=n.asname)
        return self._visit_any_import(node)

    def visit_ImportFrom(self, node):
        for n in node.names:
            self.validate_imports(node.module, n.name, alias=n.asname)
        return self._visit_any_import(node)

    def validate_imports(self, import_path, module_name=None, alias=None):
        self.valid_import_path(import_path, module_name)

    def _visit_any_import(self, node):
        self.generic_visit(node)
        return node

    '''
    Why are we even doing any logic instead of just failing on visiting these?
    '''
    def visit_ClassDef(self, node):
        self.log.error("Classes are not allowed in Seneca contracts")
        # self._is_success = False
        # self.generic_visit(node)
        raise CompilationException
        # return node

    def visit_AsyncFunctionDef(self, node):
        self.log.error("Async functions are not allowed in Seneca contracts")
        # self._is_success = False
        # self.generic_visit(node)
        raise CompilationException

    def visit_Assign(self, node):
        # resource_names, func_name = Assert.valid_assign(node, Parser.parser_scope)
        self.generic_visit(node)
        return node

    def visit_AugAssign(self, node):
        # raghu todo checks here?
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        # raghu todo do we need any other checks against calling some system functions here?
        self.is_datatype(node)
        self.generic_visit(node)
        return node

    def visit_Num(self, node):
        # NOTE: Integers are important for indexing and slicing so we cannot replace them. They also will not suffer
        #       from rounding issues.
        # are any types we don't allow right now? raghu todo
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        self.no_nested_imports(node)
        for d in node.decorator_list:
            if d.id in ('seneca_export'):
                self._is_one_export = True
        self.generic_visit(node)
        return node

    def _reset(self):
        self._functions = []
        self._is_one_export = False
        self._is_success = True

    def _final_checks(self):
        if not self._is_one_export:
            self.log.error("Need atleast one method with @seneca_export() decorator that outside world use to interact with this contract")
            self._is_success = False
    
    def _collect_function_defs(self, root):
        for node in ast.walk(root):
            if isinstance(node, ast.FunctionDef):
                self._functions.append(node.name)
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for n in node.names:
                    if n.asname:
                        self._functions.append(n.asname)
                    else:
                        self._functions.append(n.name.split('.')[-1])

    def check(self, ast_tree):
        self._reset()
        # pass 1 - collect function def and imports
        self._collect_function_defs(ast_tree)
        self.visit(ast_tree)
        self._final_checks()
        return self._is_success


