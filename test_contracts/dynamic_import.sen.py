@export
def execute_function(contract_name, func_name, args=(), kwargs={}):
    res = __executor__.execute_function(contract_name, func_name, rt['sender'], args=args, kwargs=kwargs)
    assert res['status'] == 'success', 'Dynamic call to {}.{} has failed'.format(contract_name, func_name)
    return res['output']