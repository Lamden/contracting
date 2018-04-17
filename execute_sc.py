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
import importlib

from parser_internal import basic_ast_whitelist

seneca_lib_path = os.path.join(os.path.realpath(__file__), 'seneca')


# Load module from file, return code as string
# In real application, a different function will be provided from Cilantro,
#   which will pull module code from block chain.
def test_seneca_loader(sc_dir, mod_name):
    m_path = os.path.join(sc_dir, (mod_name + '.seneca'))
    # print("Loading %s" % m_path)
    return open(m_path, 'r').read()


def ast_import_decoder(item):
    """Analyzes import statement in smart contract.
    Decide if the import is valid and supported.
    Figure out whether the module being imported is a smart contract or a Seneca lib
    Return a dict with detailed information about the import.
    """
    def is_seneca(module_path):
        return module_path.split('.')[0] == 'seneca'

    def is_smart_contract(module_path):
        # TODO: Must implement this!!!
        return True

    ret = {
        'module_type': None, # [seneca_lib, smart_contract]
        'module_path': None, # (must be populated)
        'qualified_name': None, # (either string or None)
        'specific_names_in_mod': None, # (either list of pairs (attr, (optional asname), or None)
    }

    item_type = type(item)

    path_getters = {
        ast.Import: lambda x: x.names[0].name,
        ast.ImportFrom: lambda x: item.module
    }

    assert item_type in path_getters.keys(), "AST node is not an import"

    ret['module_path'] = path_getters[item_type](item)

    if is_seneca(ret['module_path']):
        ret['module_type'] = 'seneca'
    elif is_smart_contract(ret['module_path']):
        ret['module_type'] = 'smart_contract'
    else:
        # TODO: custom exception types, also, consider moving this
        raise Exception("Dissallowed import, not from Seneca or smart contract")

    if type(item) == ast.Import:
        # TODO: add this functionality, note, this is why return type is a list of return objects
        assert len(item.names) == 1, "Seneca doesn't currently support multiple imports in one line"
        as_name = item.names[0].asname
        ret['qualified_name'] = as_name if as_name else ret['module_path']
    else:
        # TODO: add handling for * wildcard imports
        ret['specific_names_in_mod'] = {x.name:x.asname for x in item.names}

    return [ret]


def is_ast_import(item):
    t = type(item)
    return t == ast.ImportFrom or t == ast.Import


# TODO: make sure this loads modules exactly once per caller_id
def seneca_lib_loader(module_path, global_run_data, this_contract_run_data):
    print('Importing module %s' % module_path)

    x = importlib.import_module(module_path)

    if module_path == 'seneca.runtime':
        return x.make_exports(global_run_data, this_contract_run_data)
    else:
        # TODO: implement complete seneca_internal and DRY this out, make internal attrs match runtime.py
        si = Empty()
        si.called_by_internal = False
        si.smart_contract_caller = global_run_data['caller_user_id']
        si.this_contract_address = this_contract_run_data['contract_id']
        x.seneca_internal = si

        assert hasattr(x, 'exports'), "Imported module %s doesn't have any exports" % module_path
        assert x.exports is not None, "Imported module %s has exports set to None" % module_path

        return x.exports


class Empty(object):
    pass


def build_import_object(call_chain):

    def f(call_chain, obj):
        if not call_chain:
            return obj
        else:
            attr = call_chain.pop()
            # TODO: come up with a cleaner way to construct object
            outer_obj = Empty()
            setattr(outer_obj, attr, obj)
            return f(call_chain, outer_obj)

    return f(call_chain, Empty())


def append_sandboxed_scope(scope, import_descriptor, exports):
    """ Given:
    * A scope (which will be bound to a smart contract to be run)
    * import_descriptor, which has info on how the objects should be bound to the scope, e.g. 'as' another name, non-qualified, etc
    * exports, objects exported from a called module, ready to be bound to a scope

    Doesn't return anything, just mutates the scope as needed.
    """
    qn = import_descriptor['qualified_name']
    if qn:
        if '.' in qn:
            call_chain = qn.split('.')
            last_in_chain = call_chain.pop()
            imp_obj = build_import_object(call_chain)
        else:
            # print('**** Setting scope name: %s to %s' % (qn, str(exports)))
            # print(type(exports))
            # print(exports)
            scope[qn] = namedtuple("Exports", exports.keys())(*exports.values())
    else:
        specific_names = import_descriptor['specific_names_in_mod']

        if specific_names:
            #Specific names is a dict, k=name, v=asname
            for real_name, as_name in specific_names.items():
                name = as_name if as_name else real_name
                scope[name] = exports[real_name]
        else:
            scope.update(exports)


def execute_contract(g lobal_run_data, this_contract_run_data, contract_str, is_main=False, module_loader=None):
    # TODO: remove search_path in module_runner invocation below.
    """
    # TODO: Refactor
    # TODO: make sure we can do 'from foo import *'
    # TODO: complex validation
    # TODO: Blacklist built-in functions we don't want
    #   Or just override __built_ins__ with a restricted list
    # TODO: Traverse and make sure total imports doesn’t exceed the limit
    # TODO: Static type inference and checks
    # TODO: Wrap execution with some limiters/metering (like Gas), memory limit,
    #   recursion, limit (sys.setrecursionlimit(limit))
    # TODO: Keep a list of imported modules, don't rerun the same module.
    # This may not be quite the right thing to do, completely wrong for storage
    # API which must know the caller and control data mutation per caller.
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
    # TODO: see what is leaked through stack frame/ global frame
    # TODO: see what we can limit through editing builtins
    """
    assert module_loader is not None, 'No module loader provided'

    #  Parse Seneca smart contract, generate AST
    smart_contract_ast = ast.parse(contract_str)

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
    new_ast_body = []
    for item in smart_contract_ast.body:
        if is_ast_import(item):
            import_list = ast_import_decoder(item)

            for imp in import_list:
                if imp['module_type'] == 'seneca':
                    # print(imp)
                    s_exports = seneca_lib_loader(imp['module_path'], global_run_data, this_contract_run_data)
                    # print(s_exports)
                    append_sandboxed_scope(module_scope, imp, s_exports)
                    # mount_exports(module_scope, imp, s_exports)

                elif imp['module_type'] == 'smart_contract':
                    # print('smart_contract import not implemented')
                    downstream_contract_run_data, downstream_contract_str = module_loader(imp['module_path'])
                    c_exports = execute_contract(global_run_data,
                                                 downstream_contract_run_data,
                                                 downstream_contract_str,
                                                 is_main=False,
                                                 module_loader=module_loader)

                    append_sandboxed_scope(module_scope, imp, c_exports._asdict())
                else:
                   # TODO: custom exception types, also, consider moving this
                   raise Exception("Dissallowed import, not from Seneca or smart contract")
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
