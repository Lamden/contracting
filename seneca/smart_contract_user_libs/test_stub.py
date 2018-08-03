'''
Seneca test import module, displays caller data.
'''

# engine injected global var only available within Seneca library modules, not in smart contracts
# engine.caller

def _print_caller_data():
    print(seneca_internal.called_by_internal)


exports = {
   'print_caller_data': _print_caller_data
}


def run_tests(_):
    '''
    # TODO: Write tests for this module.
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
