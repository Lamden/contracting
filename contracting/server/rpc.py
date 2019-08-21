from ..db.driver import ContractDriver
from ..execution.executor import Executor
from ..compilation.compiler import ContractingCompiler

import ast

driver = ContractDriver()
compiler = ContractingCompiler()

NO_CONTRACT = 1
NO_VARIABLE = 2


def get_contract(name: str):
    code = driver.get_contract(name)

    if code is None:
        return {
            'status': NO_CONTRACT
        }

    return code


def get_methods(contract: str):
    contract_code = driver.get_contract(contract)

    if contract_code is None:
        return {
            'status': NO_CONTRACT
        }

    tree = ast.parse(contract_code)

    function_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    funcs = []
    for definition in function_defs:
        func_name = definition.name
        kwargs = [arg.arg for arg in definition.args.args]

        if not func_name.startswith('__'):
            funcs.append({
                'name': func_name,
                'arguments': kwargs
            })

    return funcs


def get_var(contract: str, variable: str, key: str):
    contract_code = driver.get_contract(contract)

    if contract_code is None:
        return {
            'status': NO_CONTRACT
        }

    # Multihashes don't work here
    # Make contract driver deal with this so we can abstract it later
    if key is None:
        response = driver.get('{}.{}'.format(contract, variable))
    else:
        response = driver.get('{}.{}:{}'.format(contract, variable, key))

    if response is None:
        return {
            'status': NO_VARIABLE
        }

    return {
        'value': response
    }


def get_vars(contract: str):
    pass


def run(transaction: dict):
    pass


def run_all(transactions: list):
    pass


def lint(code: str):
    tree = ast.parse(code)
    violations = compiler.linter.check(tree)

    return_dict = {
        'violations': [],
    }

    if violations is not None:
        return_dict['violations'] = violations

    return return_dict


def compile(code: str):
    compiled_code = compiler.parse_to_code(code)

    return {
        'compiled_code': compiled_code
    }


# String to callable map for strict RPC capabilities. Explicit for a reason!
command_map = {
    'get_contract': get_contract,
    'get_var': get_var,
    'get_vars': get_vars,
    'run': run,
    'run_all': run_all,
    'lint': lint,
    'compile': compile
}


# Single function call to map RPC command to an actual Python function. Allows the server to just call this.
def process_json_rpc_command(payload: dict):
    command = payload.get('command')
    arguments = payload.get('arguments')

    if command is None or arguments is None:
        return

    func = command_map.get(command)

    if func is None:
        return

    return func(**arguments)
