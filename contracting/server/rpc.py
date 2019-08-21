def get_contract(name: str):
    pass


def get_var(contract: str, variable: str, key: str):
    pass


def get_vars(contract: str):
    pass


def run(transaction: dict):
    pass


def run_all(transactions: list):
    pass


def lint(code: str):
    pass


def compile(code: str):
    pass


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


def process_json_rpc_command(payload: dict):
    command = payload.get('command')
    arguments = payload.get('arguments')

    if command is None or arguments is None:
        return

    func = command_map.get(command)

    if func is None:
        return

    return func(**arguments)
