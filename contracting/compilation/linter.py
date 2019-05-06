import ast

from .. import config

from ..logger import get_logger
from ..compilation.whitelists import ALLOWED_AST_TYPES, VIOLATION_TRIGGERS


class Linter(ast.NodeVisitor):

    def __init__(self):
        self.log = get_logger('Seneca.Parser')
        self._violations = []
        self._functions = []
        self._is_one_export = False
        self._is_success = True
        self._constructor_visited = False

    def ast_types(self, t, lnum):
        if type(t) not in ALLOWED_AST_TYPES:
            str = "Line {}".format(lnum) + " : " + VIOLATION_TRIGGERS[0] + " : {}" .format(type(t).__name__)
            self._violations.append(str)
            self._is_success = False

    def not_system_variable(self, v, lnum):

        if v.startswith('_'):
            str = "Line {} : ".format(lnum) + VIOLATION_TRIGGERS[1] + " : {}" .format(v)
            self._violations.append(str)
            self._is_success = False

    def no_nested_imports(self, node):
        for item in node.body:
            if type(item) in [ast.ImportFrom, ast.Import]:
                str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[2]
                self._violations.append(str)
                self._is_success = False

    def visit_Name(self, node):
        self.not_system_variable(node.id, node.lineno)
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        self.not_system_variable(node.attr, node.lineno)
        self.generic_visit(node)
        return node

    def visit_Import(self, node):
        # for n in node.names:
        #     self.validate_imports(n.name, alias=n.asname, lnum = node.lineno)
        return node


    def visit_ImportFrom(self, node):
        str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[3]
        self._violations.append(str)
        self._is_success = False

    '''
    Why are we even doing any logic instead of just failing on visiting these?
    '''
    def visit_ClassDef(self, node):
        # self.log.error("Classes are not allowed in Seneca contracts")
        str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[5]
        self._violations.append(str)
        self._is_success = False
        self.generic_visit(node)
        #raise CompilationException
        return node

    def visit_AsyncFunctionDef(self, node):
        # self.log.error("Async functions are not allowed in Seneca contracts")
        str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[6]
        self._violations.append(str)

        self._is_success = False
        self.generic_visit(node)
        # raise CompilationException
        return node

    def visit_Assign(self, node):
        # resource_names, func_name = Assert.valid_assign(node, Parser.parser_scope)
        if isinstance(node.value, ast.Call) and not isinstance(node.value.func, ast.Attribute) and node.value.func.id in config.ORM_CLASS_NAMES:
            if node.value.func.id in ['Variable', 'Hash']:
                kwargs = [k.arg for k in node.value.keywords]
                if 'contract' in kwargs or 'name' in kwargs:
                    self._is_success = False
                    str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[10]
                    self._violations.append(str)
            if ast.Tuple in [type(t) for t in node.targets] or isinstance(node.value, ast.Tuple):
                self._is_success = False
                str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[11]
                self._violations.append(str)

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
            str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[9] + \
                  ": Detected: {} MAX limit: 1".format(len(node.decorator_list))
            self._violations.append(str)
            self._is_success = False

        for d in node.decorator_list:
            # Only allow decorators from the allowed set.
            if d.id not in config.VALID_DECORATORS:
                str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[7] + \
                      ": valid list: {}".format(d.id, config.VALID_DECORATORS)
                self._violations.append(str)
                self._is_success = False

            if d.id == config.EXPORT_DECORATOR_STRING:
                self._is_one_export = True

            if d.id == config.INIT_DECORATOR_STRING:
                if self._constructor_visited:
                    str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[8]
                    self._violations.append(str)
                    self._is_success = False
                self._constructor_visited = True

        self.generic_visit(node)
        return node

    def _reset(self):
        self._violations = []
        self._functions = []
        self._is_one_export = False
        self._is_success = True
        self._constructor_visited = False

    def _final_checks(self):
        if not self._is_one_export:
            str = "Line 0: " + VIOLATION_TRIGGERS[12]
            self._violations.append(str)
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

        if self._is_success is False:
            #print(self.dump_violations())
            return self._violations
        else:
            return None

    def dump_violations(self):
        import pprint
        pp = pprint.PrettyPrinter(indent = 4)
        pp.pprint(self._violations)





