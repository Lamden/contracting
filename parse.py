#!/usr/bin/env python3.6

# Official AST docs: https://docs.python.org/3/library/ast.html
# Good AST docs here: http://greentreesnakes.readthedocs.io/en/latest/index.html

# ast.AST - This is the base of all AST node classes
# _fields - Each concrete class has an attribute _fields which gives the names of all child nodes.

# module._fields = (body',)

import sys
import ast
import astpretty

def pprint(*args, **kwargs):
    return astpretty.pprint(*args, **kwargs)

def dprint(x):
    xs = dir(x)
    for x in xs:
        print(x)

print("Starting Seneca...")

sc_path = sys.argv[1]

#  Parse python smart contract, generate AST
print("Loading %s" % sc_path)
sc_text = open(sc_path, 'r').read()
a = ast.parse(sc_text)

assert type(a) == ast.Module, "Unexpected input, 'a' should always be an _ast.Module"

# Basic whitelist validation
ast_type_whitelist = {
    ast.Module,
    ast.Eq,
    ast.Call,
    ast.Dict,
    ast.Attribute,
    ast.Pow,
    ast.Index,
    ast.Not,
    ast.alias,
    ast.If,
    ast.FunctionDef,
    ast.GtE,
    ast.Load,
    ast.arg,
    ast.Add,
    ast.Lambda,
    ast.ImportFrom,
    ast.Name,
    ast.Num,
    ast.BinOp,
    ast.Store,
    ast.Assert,
    ast.Assign,
    ast.Subscript,
    ast.Compare,
    ast.Return,
    ast.NameConstant,
    ast.Expr,
    ast.keyword,
    ast.Sub,
    ast.arguments,
    ast.List,
    ast.Str,
    ast.UnaryOp,
}

current_ast_types = {type(x) for x in ast.walk(a)}

illegal_ast_nodes = current_ast_types - ast_type_whitelist

wl_error_message = 'Found illegal AST node(s) in module: ' + ', '.join(
  map(str, illegal_ast_nodes)
)

assert not illegal_ast_nodes, wl_error_message

# Complex validation
# TODO: Implement this!
# * blacklist built-in functions we don't want
#   * eval



#  * Convert the user imports to some custom function that imports from blockchain smart contracts
#    * User will just write “import <some_contract_addr>”
#    * https://docs.python.org/3/reference/import.html
#    * Somewhat unrelated, when implementing custom importer for seneca smart contracts,
#      we also need to do a custom importer in the seneca lib so we don't leak functions
#      that don't belong in the smart contract execution scope.
#  * Validate smart contract imports
#    * Make sure they point to valid contracts
#    * Traverse and make sure total imports doesn’t exceed the limit
#  * import our restricted lib of standard functions into scope
#  * import smart contract code into scope
#  * Run rpython, add type annotations to AST
#  * Type check (with something)
#  * Wrap execution with some limiters
#    * Memory limit (ulimit or whatever)
#    * recursion limit (sys.setrecursionlimit(limit))
#  * Execute
#    Todo: Possibly with custom executer that meters execution cycles (either hard limit or Gas equivalent)
#pprint(a)


try:



    def import_as_mod(mod_ast):
        # XXX: This is probably not the right way to do this,
        # Look at importlib source to see how cpython does this
        d = dict(locals(), **globals())
        d['__name__'] = '__imported_module__'
        exec(compile(mod_ast, filename="<ast>", mode="exec"), d, d)
        return d['exports']


    def import_as_main(mod_ast):
        # XXX: This is probably not the right way to do this,
        # Look at importlib source to see how cpython does this
        d = dict(locals(), **globals())
        d['__name__'] = '__main__'
        exec(compile(mod_ast, filename="<ast>", mode="exec"), d, d)



except:
    print('\n\n\n')
    raise
