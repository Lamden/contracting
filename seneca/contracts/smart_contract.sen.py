@export
def submit_contract(contract_name, code_str):
    code_obj, resources, methods = __executor__.compile(contract_name, code_str)
    contract = {
        'code_str': code_str,
        'code_obj': code_obj,
        'author': rt['origin'],
        'resources': resources,
        'methods': methods
    }
    __executor__.set_contract(contract_name, **contract, override=False)
    return contract

@export
def get_contract(contract_name):
    return __executor__.get_contract(contract_name)
