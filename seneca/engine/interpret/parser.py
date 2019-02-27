from seneca.engine.interpret.scope import Export, Seed, Function
from seneca.constants.whitelists import SAFE_BUILTINS, ALLOWED_DATA_TYPES
from seneca.engine.interpret.utils import Plugins, Assert, CompilationException
from seneca.libs.decimal import make_decimal
from seneca.libs.resource import set_resource_limits
from collections import defaultdict
import ast, copy


class Parser:
    basic_scope = {
        'export': Export(),
        'seed': Seed(),
        '__set_resources__': set_resource_limits,
        '__decimal__': make_decimal,
        '__function__': Function(),
        '__builtins__': SAFE_BUILTINS
    }

    parser_scope = None
    seed_tree = None
    child = None
    initialized = False

    @classmethod
    def initialize(cls):
        if not cls.initialized:
            cls.parser_scope = {
                'ast': None,
                'callstack': [],
                'exports': {},
                'imports': {},
                'resources': {},
                'protected': defaultdict(set)
            }
            cls.initialized = True

    @classmethod
    def reset(cls):
        cls.initialize()
        cls.parser_scope.update({
            'imports': {},
            '__args__': (),
            '__kwargs__': {}
        })
        cls.parser_scope.update(cls.basic_scope)
        cls.parser_scope['protected']['global'].update(cls.basic_scope.keys())
        cls.seed_tree = None

    @staticmethod
    def parse_ast(code_str):
        # Parse tree
        tree = ast.parse(code_str)
        Parser.seed_tree = copy.deepcopy(tree)
        Parser.seed_tree.body = []
        tree = NodeTransformer().visit(tree)
        ast.fix_missing_locations(tree)

        return Parser.seed_tree


class NodeTransformer(ast.NodeTransformer):

    @property
    def contract_name(self):
        return Parser.parser_scope['rt']['contract']

    @property
    def resource_list(self):
        return [k for k, v in self.resource.items() if v == 'Resource']

    @property
    def resource(self):
        if not Parser.parser_scope['resources'].get(self.contract_name):  # Default dict not marshallable
            Parser.parser_scope['resources'][self.contract_name] = {}
        return Parser.parser_scope['resources'][self.contract_name]

    def generic_visit(self, node):
        Assert.ast_types(node)
        return super().generic_visit(node)

    def visit_Name(self, node):
        Assert.not_system_variable(node.id)
        if Parser.parser_scope['ast'] in ('seed', 'export', 'func') \
                and node.id in self.resource_list:
            self.generic_visit(node)
            return Plugins.resource_reassignment(node.id, node.ctx)
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
        obj_name = Assert.valid_import_path(import_path, module_name, self.contract_name)
        if obj_name:
            Assert.is_not_resource(obj_name, Parser.parser_scope)
            call_name = '{}.{}'.format(import_path.split('.')[-1], obj_name)
            Parser.parser_scope['imports'][call_name] = True
        Parser.parser_scope['protected'][self.contract_name].add(module_name)
        if Parser.parser_scope['ast'] != '__system__':
            Parser.parser_scope['ast'] = 'import'
        Parser.seed_tree.body.append(node)
        self.generic_visit(node)
        if Parser.parser_scope['ast'] != '__system__':
            Parser.parser_scope['ast'] = None
        return node

    def visit_Assign(self, node):
        resource_name, func_name = Assert.valid_assign(node, Parser.parser_scope)
        if resource_name and func_name:
            if func_name == 'Resource':
                node.value.args = [ast.Str(resource_name)]
            self.resource[resource_name] = func_name
            Parser.seed_tree.body.append(node)
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        if Parser.parser_scope['ast'] in ('seed', 'export', 'func'):
            Assert.not_datatype(node)
            return node
        self.generic_visit(node)
        return node

    def visit_AugAssign(self, node):
        Assert.is_protected(node.target, Parser.parser_scope)
        self.generic_visit(node)
        return node

    def visit_Num(self, node):
        # NOTE: Integers are important for indexing and slicing so we cannot replace them. They also will not suffer
        #       from rounding issues.
        if isinstance(node.n, float):  # or isinstance(node.n, int):
            return ast.Call(func=ast.Name(id='__decimal__', ctx=ast.Load()),
                            args=[node], keywords=[])
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        if Parser.parser_scope['ast'] == None:
            Assert.no_nested_imports(node)
            ast_set = False
            for d in node.decorator_list:
                if d.id in ('export', 'seed'):
                    Parser.parser_scope['ast'] = d.id
                    ast_set = True
            if not ast_set:
                Parser.parser_scope['ast'] = 'func'
            if Parser.parser_scope['ast'] in ('export', 'seed', 'func'):
                self.generic_visit(node)
            Parser.parser_scope['ast'] = None

        node.decorator_list.append(
            ast.Name(id='__function__', ctx=ast.Load())
        )
        Parser.seed_tree.body.append(node)
        return node
