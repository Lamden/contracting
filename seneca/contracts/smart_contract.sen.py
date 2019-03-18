@export
def submit_contract(contract_name, code_str):
    __executor__.concurrency = rt['concurrency']
    __executor__.metering = rt['metering']
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

@export
def execute_function(contract_name, func_name, kwargs={}):
    res = __executor__.execute_function(contract_name, func_name, rt['sender'], kwargs=kwargs)
    assert res['status'] == 'success', 'Dynamic call to {}.{} has failed'.format(contract_name, func_name)
    return res['output']

@export
def import_contract(contract_name):
    return __executor__.dynamic_import(contract_name, rt['sender'])
