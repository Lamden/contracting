from collections import namedtuple
'''
Note: at least for now, runtime is a special module and is handled differently by the module loader.
  Why? Currently for development all smart contracts are loaded into the same
    python interpretter instance. This will not be the case in production code,
    the will be isolated in containers. Runtime data is unique for each smart
    contract but since python modules are singletons runtime data would be the
    same for all contracts in execution tree.

TODO:
  * Decide if we want to present call chain
  * Finalize api (names of exports), make those names consistent in execute_sc and elsewhere
'''

def make_n_tup(d):
    # TODO: make sure this is good/safe
    return namedtuple('_', ' '.join(d.keys()))(**d)


def make_exports(global_runtime_data, this_runtime_data):
    caller = global_runtime_data['call_stack'][-1][1] if len(global_runtime_data['call_stack']) > 0 else '__main__'

    # author - the original author of the contract
    # sender - the wallet that is sending the contract
    # caller - the top of the call stack
    # call_stack - the list of callers up to this point
    # now - execution datetime

    return {
        'this': make_n_tup({
            'author': this_runtime_data['author'],
            'now': this_runtime_data['now'],
        }),
        'global_run_data': make_n_tup({
            'author': global_runtime_data['caller_user_id'],
            'address': global_runtime_data['caller']
        }),
        'call_stack': global_runtime_data['call_stack'],
        'caller': caller
    }

def run_tests(_):
    '''
    # TODO: Write tests for this module.
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
