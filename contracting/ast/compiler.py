import ast
import astor

from contracting import config

from contracting.logger import get_logger
from contracting.ast.linter import Linter
import copy

class ContractingCompiler(ast.NodeTransformer):
    def __init__(self, module_name='__main__', linter=Linter()):
        self.log = get_logger('Contracting.Compiler')
        self.module_name = module_name
        self.linter = linter
        self.lint_alerts = None
        self.constructor_visited = False
        self.private_expr = set()
        self.visited_expr = set()  # store the method visits

    def parse(self, source: str, lint=True):
        self.constructor_visited = False

        tree = ast.parse(source)

        if lint:
            self.lint_alerts = self.linter.check(tree)
            # ast.fix_missing_locations(tree)

        tree = self.visit(tree)

        if self.lint_alerts is not None:
            raise Exception(self.lint_alerts)

        # check all visited nodes and see if they are actually private

        for node in self.visited_expr:
            try:
                if isinstance(node.value, ast.Call) and node.value.func.id in self.private_expr:
                    node.value.func.id = self.privatize(node.value.func.id)
            except:
                pass

        ast.fix_missing_locations(tree)

        # reset state
        self.private_expr = set()
        self.visited_expr = set()

        return tree

    @staticmethod
    def privatize(s):
        return '{}{}'.format(config.PRIVATE_METHOD_PREFIX, s)

    def compile(self, source: str, lint=True):
        tree = self.parse(source, lint=lint)

        compiled_code = compile(tree, '<ast>', 'exec')

        return compiled_code

    def parse_to_code(self, source, lint=True):
        tree = self.parse(source, lint=lint)
        code = astor.to_source(tree)
        return code

    def visit_FunctionDef(self, node):

        # Presumes all decorators are valid, as caught by linter.
        if node.decorator_list:
            # Presumes that a single decorator is passed. This is caught by the linter.
            decorator = node.decorator_list.pop()

            # change the name of the init function to '____' so it is uncallable except once
            if decorator.id == config.INIT_DECORATOR_STRING:
                node.name = '____'
        else:
            self.private_expr.add(node.name)
            node.name = self.privatize(node.name)

        # body = copy.deepcopy(node.body)
        # node.body = [ast.With(items=[ast.withitem(
        #                         context_expr=ast.Name(
        #                             id='__Context()',
        #                             ctx=ast.Load()),
        #                         optional_vars=ast.Name(
        #                             id='ctx',
        #                             ctx=ast.Store()
        #                         )
        #                     )],
        #                         body=body)]

        self.generic_visit(node)

        return node

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call) and not isinstance(node.value.func,
                                                               ast.Attribute) and node.value.func.id in config.ORM_CLASS_NAMES:
            node.value.keywords.append(ast.keyword('contract', ast.Str(self.module_name)))
            node.value.keywords.append(ast.keyword('name', ast.Str(node.targets[0].id)))

        return node

    def visit_Call(self, node):
        return node

    def visit_Expr(self, node):
        # keeps track of visited expressions for private method prefixing after parsing tree
        if isinstance(node.value, ast.Call):
            self.visited_expr.add(node)

        return node
