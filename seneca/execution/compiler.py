import ast

from seneca.logger import get_logger
from seneca.execution.linter import Linter
from seneca.db.orm import CLASS_NAMES

from seneca.execution.runtime import rt

PRIVATE_METHOD_PREFIX = '__'
EXPORT_DECORATOR_STRING = 'seneca_export'
INIT_DECORATOR_STRING = 'seneca_construct'
VALID_DECORATORS = {EXPORT_DECORATOR_STRING, INIT_DECORATOR_STRING}


class SenecaCompiler(ast.NodeTransformer):
    def __init__(self, module_name=rt.ctx[-1], linter=Linter()):
        self.log = get_logger('Seneca.Compiler')
        self.module_name = module_name
        self.linter = linter
        self.constructor_visited = False

    def parse(self, source: str, lint=True):
        self.constructor_visited = False

        tree = ast.parse(source)

        if lint:
            tree = self.linter.visit(tree)
            ast.fix_missing_locations(tree)

        tree = self.visit(tree)
        ast.fix_missing_locations(tree)

        return tree

    def compile(self, source: str, lint=True):
        tree = self.parse(source, lint=lint)
        compiled_code = compile(tree, '<ast>', 'exec')

        return compiled_code

    def visit_FunctionDef(self, node):
        # Presumes all decorators are valid, as caught by linter.
        if node.decorator_list:
            # Presumes that a single decorator is passed. This is caught by the linter.
            d = node.decorator_list.pop()

        else:
            node.name = '__{}'.format(node.name)

        return node

    def visit_Assign(self, node):
        #print("Node.value: {}".format(node.value))
        if isinstance(node.value, ast.Call) and node.value.func.id in CLASS_NAMES:
            if node.value.func.id in ['Variable', 'Hash']:
                assert node.value.keywords == [], 'Keyword overloading not allowed.'
            assert len(node.targets) == 1, 'Multiple targets to an ORM definition is not allowed.'
            node.value.keywords.append(ast.keyword('contract', ast.Str(self.module_name)))
            node.value.keywords.append(ast.keyword('name', ast.Str(node.targets[0].id)))

        return node

    # def visit_AugAssign(self, node):
    #     self._global_variables.append(node.target.id)
    #     return node
    #
    # def visit_AnnAssign(self, node):
    #     self._global_variables.append(node.target.id)
    #     return node
    #
    # # globals shouldn't be allowed
    # def visit_Global(self, node):
    #     for n in node.names:
    #         self._global_variables.append(n)
    #     return node
