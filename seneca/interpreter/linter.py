import ast

from .. import config

from .whitelists import ALLOWED_AST_TYPES
from ..logger import get_logger


class Linter(ast.NodeVisitor):
    violations = []

    def __init__(self):
        self.log = get_logger('Seneca.Parser')
        self._functions = []
        self._is_one_export = False
        self._is_success = True
        self._constructor_visited = False
        #self.driver = ContractDriver()

    @staticmethod
    def ast_types(t):
        if type(t) not in ALLOWED_AST_TYPES:
            str = "Error : Illegal AST type: {}" .format(type(t).__name__)
            Linter.violations.append(str)

    @staticmethod
    def not_system_variable(v):
        if v.startswith('_'):
            str = "Error : Incorrect use of <_> access denied for var : {}".format(v)
            Linter.violations.append(str)

    @staticmethod
    def no_nested_imports(node):
        for item in node.body:
            if type(item) in [ast.ImportFrom, ast.Import]:
                str = "Error : Nested import is illegal"
                Linter.violations.append(str)

    def visit_Name(self, node):
        self.not_system_variable(node.id)
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
        str = 'ImportFrom ast nodes not yet supported.'
        Linter.violations.append(str)

    def validate_imports(self, import_path, module_name=None, alias=None):
        if self.driver.get_contract(import_path) is None:
            str = 'Contract named "{}" does not exist in state.'.format(import_path)
            Linter.violations.append(str)

    def _visit_any_import(self, node):
        self.generic_visit(node)
        return node

    '''
    Why are we even doing any logic instead of just failing on visiting these?
    '''
    def visit_ClassDef(self, node):
        self.log.error("Classes are not allowed in Seneca contracts")
        self._is_success = False
        self.generic_visit(node)
        #raise CompilationException
        return node

    def visit_AsyncFunctionDef(self, node):
        self.log.error("Async functions are not allowed in Seneca contracts")
        self._is_success = False
        self.generic_visit(node)
        # raise CompilationException
        return node

    def visit_Assign(self, node):
        # resource_names, func_name = Assert.valid_assign(node, Parser.parser_scope)
        if isinstance(node.value, ast.Call) and node.value.func.id in config.ORM_CLASS_NAMES:
            if node.value.func.id in ['Variable', 'Hash']:
                if len(node.value.keywords) > 0:
                    str = 'Keyword overloading not allowed for ORM assignments.'
                    Linter.violations.append(str)
            if len(node.targets) > 1:
                str = 'Multiple targets to an ORM definition is not allowed.'
                Linter.violations.append(str)

        self.generic_visit(node)
        return node

    def visit_AugAssign(self, node):
        # raghu todo checks here?
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        # raghu todo do we need any other checks against calling some system functions here?
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

        # Only allow 1 decorator per function definition.
        if len(node.decorator_list) > 1:
            str = 'Function definition can only contain 1 decorator. Currently contains {}.'\
                .format(len(node.decorator_list))
            Linter.violations.append(str)

        for d in node.decorator_list:
            # Only allow decorators from the allowed set.
            if d.id not in config.VALID_DECORATORS:
                str = '{} is an invalid decorator. Must be one of {}'.format(d.id,
                                                                             config.VALID_DECORATORS)
                Linter.violations.append(str)
            if d.id == config.EXPORT_DECORATOR_STRING:
                self._is_one_export = True

            if d.id == config.INIT_DECORATOR_STRING:
                if self._constructor_visited:
                    str = 'Multiple constructors not allowed.'
                    Linter.violations.append(str)
                self._constructor_visited = True

        self.generic_visit(node)
        return node

    def _reset(self):
        self._functions = []
        self._is_one_export = False
        self._is_success = True
        self._constructor_visited = False

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

    @staticmethod
    def dump_violations():
        import pprint
        pp = pprint.PrettyPrinter(indent = 4)
        pp.pprint(Linter.violations)





