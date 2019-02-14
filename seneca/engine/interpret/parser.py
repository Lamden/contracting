from seneca.engine.interpret.scope import Export, Seed, Function
from seneca.constants.whitelists import SAFE_BUILTINS
from seneca.engine.interpret.utils import Plugins, Assert
import ast, copy

class Parser:

    basic_scope = {
        'export': Export(),
        'seed': Seed(),
        '__function__': Function(),
        '__builtins__': SAFE_BUILTINS
    }

    parser_scope = {}
    executor_scope = None
    seed_tree = None
    executor = None

    @classmethod
    def reset(cls, top_level_contract=None):
        cls.parser_scope = {
            'callstack': [top_level_contract],
            'exports': {},
            'imports': {},
            'resources': {},
            'protected': set()
        }
        cls.parser_scope.update(cls.basic_scope)
        cls.seed_tree = None

    @staticmethod
    def parse_ast(code_str):
        # Add plugins
        code_str = Plugins.fixed_precision(code_str)
        code_str = Plugins.resource_limits(code_str)

        # Parse tree
        tree = ast.parse(code_str)
        Parser.seed_tree = copy.deepcopy(tree)
        Parser.seed_tree.body = []
        tree = NodeTransformer().visit(tree)
        ast.fix_missing_locations(tree)

        return Parser.seed_tree

class NodeTransformer(ast.NodeTransformer):

    def generic_visit(self, node):
        Assert.ast_types(node)
        return super().generic_visit(node)

    def visit_Name(self, node):
        Assert.not_system_variable(node.id)
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        Assert.not_system_variable(node.attr)
        self.generic_visit(node)
        return node

    def visit_Import(self, node):
        return self._visit_any_import(node, node.names[0].name)


    def visit_ImportFrom(self, node):
        return self._visit_any_import(node, node.module, module_name=node.names[0].name)

    def _visit_any_import(self, node, import_path, module_name=None):
        Assert.valid_import_path(import_path, module_name, Parser.parser_scope['callstack'][-1])
        if not Parser.parser_scope['exports'].get(import_path):
            Parser.parser_scope['imports'][import_path] = True
        Parser.parser_scope['protected'].add(import_path)
        # Seneca.prevalidated.body.append(node)
        # Seneca.postvalidated.body.append(node)
        Parser.seed_tree.body.append(node)
        self.generic_visit(node)
        return node

    def visit_Assign(self, node):
        for target in node.targets:
            if type(target) == ast.Tuple:
                items = []
                for item in target.elts:
                    Assert.is_protected(item, Parser.parser_scope)
                    items.append(item.id)
                val = None
                if type(node.value) == ast.Call:
                    val = node.value.func.id
                elif type(target) == ast.Tuple:
                    val = 'tuple'
                Parser.parser_scope['resources'][', '.join(items)] = val
            elif type(node.value) == ast.Call:
                if hasattr(node.value.func, 'id'):
                    Parser.parser_scope['resources'][target.id] = node.value.func.id
                Assert.is_protected(target, Parser.parser_scope)
            else:
                if type(target) == ast.Subscript:
                    name = target.value.id
                else:
                    name = target.id
                Parser.parser_scope['resources'][name] = node.value.__class__.__name__
                Assert.is_protected(target, Parser.parser_scope)

        if type(node.value) == ast.Call:
            Parser.seed_tree.body.append(node)

        self.generic_visit(node)
        return node

    def visit_AugAssign(self, node):
        Assert.is_protected(node.target, Parser.parser_scope)
        self.generic_visit(node)
        return node

    def visit_Num(self, node):
        if isinstance(node.n, float) or isinstance(node.n, int):
            return ast.Call(func=ast.Name(id='make_decimal', ctx=ast.Load()),
                            args=[node], keywords=[])
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        Assert.no_nested_imports(node)
        for item in node.decorator_list:
            if item.id == 'export':
                Parser.parser_scope['exports'][node.name] = [arg.arg for arg in node.args.args]
            elif item.id == 'seed':
                pass
        Parser.seed_tree.body.append(node)
        return node