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

    def parse(self, source: str, lint=False):
        self.constructor_visited = False

        tree = ast.parse(source)

        if lint:
            tree = self.linter.visit(tree)
            ast.fix_missing_locations(tree)

        tree = self.visit(tree)
        ast.fix_missing_locations(tree)

        return tree

    def compile(self, source: str, lint=False):
        tree = self.parse(source, lint=lint)
        compiled_code = compile(tree, '<ast>', 'exec')

        return compiled_code

    def visit_FunctionDef(self, node):
        if node.decorator_list:
            print(node.decorator_list)
            assert len(node.decorator_list) == 1, 'Multiple decorators on a function not allowed'

            d = node.decorator_list.pop()
            assert d.id in VALID_DECORATORS, 'Invalid Decorator passed'

            if d.id == EXPORT_DECORATOR_STRING:
                pass
            elif d.id == INIT_DECORATOR_STRING:
                assert not self.constructor_visited, 'Multiple constructors found'
                self.constructor_visited = True

        else:
            node.name = '__{}'.format(node.name)

        return node

    def visit_Assign(self, node):
        if node.value.func.id in CLASS_NAMES:
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
