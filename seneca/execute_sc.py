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
from seneca.seneca_internal.util import *

from seneca.seneca_internal.parser import basic_ast_whitelist
import seneca.seneca_internal.util as util

seneca_lib_path = os.path.join(os.path.realpath(__file__), 'seneca')


# Load module from file, return code as string
# In real application, a different function will be provided from Cilantro,
#   which will pull module code from block chain.
def test_seneca_loader(sc_dir, mod_name):
    m_path = os.path.join(sc_dir, (mod_name + '.seneca'))
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


def seneca_module_name_to_path(name):
    slashed_name = os.path.join(*name.split('.'))
    if os.path.isdir(slashed_name):
        f_path = os.path.join(slashed_name, '__init__.py')
        assert os.path.isfile(f_path)
        return f_path

    elif os.path.isfile(slashed_name + '.py'):
        return slashed_name + '.py'
    else:
        raise Exception('bad import path:' + name)


# TODO: make sure this loads modules exactly once per caller_id
def seneca_lib_loader(imp, global_run_data, this_contract_run_data, db_executer):
    assert db_executer is not None, "A mysql executer must be passed to seneca_lib_loader for contracts that use tabular data storage."
    #print(imp)

    module_path = imp['module_path']

    # Rename 'seneca' part of module path to 'smart_contract_user_libs'
    real_path = 'seneca.smart_contract_user_libs.' + '.'.join(module_path.split('.')[1:])

    #s_mod = importlib.import_module(real_path)
    mod_file_path = seneca_module_name_to_path(real_path)
    s_mod = util.manual_import(mod_file_path, real_path.split('.')[-1])

    if module_path == 'seneca.storage.tabular':
        s_mod['ex'] = db_executer
        s_mod['name_space'] = this_contract_run_data['contract_id']

        return s_mod['exports']

    elif module_path == 'seneca.storage':
        raise Exception('This feature is not implemented, for now you must import the complete module.')

    if module_path == 'seneca.runtime':
        return s_mod['make_exports'](global_run_data, this_contract_run_data)
    else:
        # TODO: implement complete seneca_internal and DRY this out, make internal attrs match runtime.py
        si = Empty()
        si.called_by_internal = False
        si.smart_contract_caller = global_run_data['caller_user_id']
        si.this_contract_address = this_contract_run_data['contract_id']
        s_mod['seneca_internal'] = si

        assert 'exports' in s_mod.keys(), "Imported module %s doesn't have any exports" % module_path
        assert s_mod['exports'] is not None, "Imported module %s has exports set to None" % module_path

        return s_mod['exports']


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

class ContractExecutionResult(object):
    def __init__(self):
        self.passed = None
        self.error_message = None
        self.exception = None

    def __str__(self):
        if self.passed:
            return "<ContractExecutionResult: SUCCESS >"
        else:
            return "<ContractExecutionResult: FAILURE: %s >" % self.error_message

    def __bool__(self):
        return self.passed


def execute_contract(*args, **kwargs):
    ret = ContractExecutionResult()

    try:
        res = _execute_contract(*args, **kwargs)
        ret.passed = True
    except Exception as e:
        ret.passed = False
        ret.error_message = str(e)
        ret.exception = e

    return ret


def _execute_contract(global_run_data, this_contract_run_data, contract_str, is_main=False, module_loader=None, db_executer=None):
    assert module_loader is not None, 'No module loader provided'

    sc_display_name = "seneca_contract_addr: %s" % this_contract_run_data['contract_id']

    #  Parse Seneca smart contract, generate AST
    sc_ast = ast.parse(contract_str)
    assert type(sc_ast) == ast.Module, "Unexpected input, 'a' should always be an _ast.Module"

    # Fail if forbidden AST nodes are found, e.g. for-loops
    basic_ast_whitelist.validate(sc_ast)

    # Create a new empty scope for module execution.
    module_scope = {}

    # Set module name, emulate the behavior of the CPython, '__main__' for the main entry point.
    module_scope['__name__'] = '__main__' if is_main else this_contract_run_data['contract_id']

    # Find all imports and recursively add them to namespaces
    new_ast_body = []

    for item in sc_ast.body:
        if is_ast_import(item):
            import_list = ast_import_decoder(item)

            for imp in import_list:
                if imp['module_type'] == 'seneca':
                    s_exports = seneca_lib_loader(imp, global_run_data, this_contract_run_data, db_executer)
                    append_sandboxed_scope(module_scope, imp, s_exports)

                elif imp['module_type'] == 'smart_contract':
                    downstream_contract_run_data, downstream_contract_str = module_loader(imp['module_path'])
                    c_exports = _execute_contract(global_run_data,
                                                 downstream_contract_run_data,
                                                 downstream_contract_str,
                                                 is_main=False,
                                                 module_loader=module_loader,
                                                 db_executer=db_executer)

                    append_sandboxed_scope(module_scope, imp, c_exports._asdict())
                else:
                   # TODO: custom exception types, also
                   raise Exception("Dissallowed import, not from Seneca or smart contract")
        else:
            # AST node isn't an import statement, just append to the output AST
            new_ast_body.append(item)

    # Replace the original AST with the new one (smart contract imports removed)
    sc_ast.body = new_ast_body

    # TODO: Make sure this is a correct and safe way to execute code.
    sc_executable = compile(sc_ast,
                                 filename=sc_display_name,
                                 mode="exec"
                         )
    exec(sc_executable, module_scope)

    if not is_main:
        # If this isn't the primary smart contract, take everythig bound to the name
        # 'exports' and return it, for addition to caller's scope, i.e. imported.
        x = module_scope['exports']
        return namedtuple(this_contract_run_data['contract_id'], x.keys())(**x)
    else:
        # TODO: figure out return for passed or failed contract
        return True
