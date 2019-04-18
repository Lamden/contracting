import ast
from seneca import config
from seneca.logger import get_logger
from seneca.execution.linter import Linter

from seneca.execution.runtime import rt

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
            node.decorator_list.pop()
        else:
            node.name = '__{}'.format(node.name)

        return node

    def visit_Assign(self, node):
        #print("Node.value: {}".format(node.value))
        if isinstance(node.value, ast.Call) and node.value.func.id in config.ORM_CLASS_NAMES:
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
