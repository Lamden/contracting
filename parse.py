#!/usr/bin/env python3.6

# # See also #
# * Official AST docs: https://docs.python.org/3/library/ast.html
# * Good AST docs here: http://greentreesnakes.readthedocs.io/en/latest/index.html
# * https://www.programiz.com/python-programming/methods/built-in/exec

# # Notes #
# * ast.AST - This is the base of all AST node classes
# * _fields - Each concrete class has an attribute _fields which gives the names
#   of all child nodes.

import sys
import ast
import astpretty
from collections import namedtuple
import os
import sys
from parser_internal import basic_ast_whitelist

# Convenience diagnostic function
def pprint(*args, **kwargs):
    return astpretty.pprint(*args, **kwargs)

# Convenience diagnostic function
def dprint(x):
    xs = dir(x)
    for x in xs:
        print(x)


# Load module from file, return code as string
# In real application, a different function will be provided from Cilantro,
#   which will pull module code from block chain.
def test_seneca_loader(mod_name):
    m_path = os.path.join(sc_dir, (mod_name + '.seneca'))
    print("Loading %s" % m_path)
    return open(m_path, 'r').read()


def module_loader(name, search_path, is_main=False, loader=test_seneca_loader):
    # TODO: complex validation
    # TODO: Blacklist built-in functions we don't want
    #   Or just override __built_ins__ with a restricted list
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
    # TODO: # We probably need a custom importer in the seneca lib so we don't
    #   leak functions that don't belong in the smart contract execution scope.

    #  Parse Seneca smart contract, generate AST
    smart_contract_ast = ast.parse(loader(name))

    assert type(smart_contract_ast) == ast.Module, \
      "Unexpected input, 'a' should always be an _ast.Module"

    # Fail if forbidden AST nodes are found, e.g. for-loops
    basic_ast_whitelist.validate(smart_contract_ast)

    # Create a new empty scope for module execution.
    module_scope = {}

    # Set module name, emulate the behavior of the CPython, overwrite name with
    # '__main__' for the main entry point.
    module_scope['__name__'] = '__main__' if is_main else name

    ## Find all imports and recursively add them to namespaces ##
    # TODO: This only handles imports in the top level of body, rest are ignored
    #   Decide what should happen if the import occurs somewhere else and
    #   implement.
    # TODO: This only handles import functionality, not security, this must be
    #   addressed.
    # TODO: Refactor, depdupe
    new_ast_body = []
    for item in smart_contract_ast.body:

        # Handle typical imports e.g. 'import foo' or 'import foo as bar'
        if type(item) == ast.Import:
            # TODO: make sure there's never more than one item in this list
            imp_node = item.names[0]
            base_module = imp_node.name.split('.')[0]

            # Don't modify seneca lib import, just append to the output AST
            if base_module == 'seneca':
                # TODO: For security we should use a restricted module loader
                new_ast_body.append(item)
            else:
                # Custom module loader
                # Don't append ast node to new_ast_body, instead run module and add
                # 'exports' to caller scope bound to name of called module.
                assert len(imp_node.name.split('.')) == 1, \
                  "Valid smart contract addresses don't contain submodules."
                # TODO: Better error message, that better explains the issue
                #   when users attempt to import stdlib or external modules.

                # mount_point is th called module's name or the 'as' name for
                #   syntax: 'import foo as bar'
                mount_point = \
                  imp_node.asname if imp_node.asname else imp_node.name

                # Bind called module's exports to caller's scope.
                module_scope[mount_point] = \
                  module_loader(imp_node.name, search_path, is_main=False)

        # Handle a from-import e.g. 'from foo import bar' (optionally 'as baz')
        elif type(item) == ast.ImportFrom:
            base_module = item.module.split('.')[0]

            # Don't modify seneca lib import, just append to the output AST
            if base_module == 'seneca':
                new_ast_body.append(item)
            else:
                assert len(item.module.split('.')) == 1, \
                  "Valid smart contract addresses don't contain submodules."
                # Custom module loader - Don't append ast node to new_ast_body,
                #   instead run module and add 'exports' to caller scope bound
                #   to name of called module.
                m_exports = module_loader(base_module, search_path,
                    is_main=False)

                for n in item.names:
                    # When funcs/values get imported from a module, the
                    #   mount_point is the name (in the callers scope) they get
                    #   bound to.
                    mount_point = n.asname if n.asname else n.name
                    module_scope[mount_point] = getattr(m_exports, n.name)
        else:
            # AST node isn't an import statement, just append to the output AST
            new_ast_body.append(item)

    # Replace the original AST with the new one (smart contract imports removed)
    smart_contract_ast.body = new_ast_body

    # TODO: Make sure this is a correct and safe way to execute code.
    exec(
      compile(smart_contract_ast, filename="<ast>", mode="exec")
      , module_scope
    )

    # If this isn't the primary smart contract, take everythig bound to the name
    #   'exports' and return it, so it can be added to the callers scope, i.e.
    #   imported.
    if not is_main:
        x = module_scope['exports']
        return namedtuple(name, x.keys())(**x)


# Run
print("Starting Seneca...")
sc_main = sys.argv[1]
sc_dir = sys.argv[2]

module_loader(sc_main, sc_dir, is_main=True)
