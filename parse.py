#!/usr/bin/env python3.6

# Official AST docs: https://docs.python.org/3/library/ast.html
# Good AST docs here: http://greentreesnakes.readthedocs.io/en/latest/index.html

# ast.AST - This is the base of all AST node classes
# _fields - Each concrete class has an attribute _fields which gives the names
# of all child nodes.

# module._fields = (body',)

# TODO: # We probably need a custom importer in the seneca lib so we don't leak
# functions that don't belong in the smart contract execution scope.

import sys
import ast
import astpretty
from collections import namedtuple
import os
import sys
from parser_internal import basic_ast_whitelist

def pprint(*args, **kwargs):
    return astpretty.pprint(*args, **kwargs)

def dprint(x):
    xs = dir(x)
    for x in xs:
        print(x)

print("Starting Seneca...")

sc_main = sys.argv[1]
sc_dir = sys.argv[2]


def test_seneca_loader(mod_name):
    m_path = os.path.join(sc_dir, (mod_name + '.seneca'))
    print("Loading %s" % m_path)
    return open(m_path, 'r').read()


# TODO: Replace default Seneca loader with Cilantro function
def module_loader(name, search_path, is_main=False, loader=test_seneca_loader):
    # TODO: complex validation
    # TODO: Blacklist built-in functions we don't want
    # TODO: Traverse and make sure total imports doesn’t exceed the limit
    # TODO: Static type inference and checks
    # TODO: Wrap execution with some limiters/metering (like Gas), memory limit,
    #   recursion, limit (sys.setrecursionlimit(limit))
    # TODO: Keep a list of imported modules, don't rerun the same module.
    # TODO: Enforce a maximum number of imports
    # TODO: Figure out how to handle imports in conditionals, it might be
    #   should probably lazy load them, with metered exectuion, eval loop may be
    #   able to inject modules exports when it evaluates the imports statements.
    # TODO: Limited safety checks for module imports only occur on body, they
    #   must be applied on the entire AST.
    # TODO: Add call depth info to Seneca runtime lib so modules have info about
    #   caller.

    #  Parse Seneca smart contract, generate AST
    a = ast.parse(test_seneca_loader(name))

    assert type(a) == ast.Module, \
      "Unexpected input, 'a' should always be an _ast.Module"

    basic_ast_whitelist.validate(a)

    # TODO: This is definitely wrong and not working correctly, fix this ASAP.
    module_scope = dict(locals(), **globals())

    # TODO: Set the module name to its actual name.
    module_scope['__name__'] = '__main__' if is_main else '__imported_module__'

    ## Find all imports and recursively add them to namespaces ##

    # XXX: This only handles imports in the top level of body, rest are ignored
    # TODO: This really only handles import functionality, not security.
    # TODO: Refactor, depdupe
    new_body = []
    for item in a.body:
        if type(item) == ast.Import:
            # TODO: make sure there's never more than one item in this list
            imp_node = item.names[0]
            base_module = imp_node.name.split('.')[0]

            if base_module == 'seneca':
                # TODO: For security we should use a restricted module loader
                #   for Seneca lib
                new_body.append(item)
            else:
                # Custom module loader
                # Don't append ast node to new_body
                # Run module and add exports to scope.
                assert len(imp_node.name.split('.')) == 1, \
                  "Valid smart contract addresses don't contain submodules."

                mount_point = \
                  imp_node.asname if imp_node.asname else imp_node.name

                module_scope[mount_point] = \
                  module_loader(imp_node.name, search_path, is_main=False)

        elif type(item) == ast.ImportFrom:
            base_module = item.module.split('.')[0]
            if base_module == 'seneca':
                new_body.append(item)
            else:
                assert len(item.module.split('.')) == 1, \
                  "Valid smart contract addresses don't contain submodules."
                # Don't append to new_body
                # TODO: run, add stuff to namespace
                print('\n')
                print(item.module)
                print(item.names[0].name)
                print(item.names[0].asname)
                print('\n')

                m_exports = module_loader(imp_node.name, search_path,
                    is_main=False)

                for n in item.names:
                    mount_point = n.asname if n.asname else n.name
                    module_scope[mount_point] = getattr(m_exports, n.name)
        else:
            # AST node isn't an import, just add it to new_body
            new_body.append(item)

    a.body = new_body

    # XXX: This is probably not the right way to do this,
    # Look at importlib source to see how cpython does this
    exec(compile(a, filename="<ast>", mode="exec"), module_scope, module_scope)

    if not is_main:
        # TODO: extract correct name from module
        x = module_scope['exports']
        return namedtuple('seneca_module', x.keys())(**x)

#module_loader(sc_main, sc_dir, is_main=True)
module_loader('simple_import', sc_dir, is_main=True)
