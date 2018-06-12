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


def make_exports(global_runtime_data, this_contract_runtime_data):
    return {
        'this_contract': make_n_tup({
            'author': this_contract_runtime_data['author'],
            'execution_datetime': this_contract_runtime_data['execution_datetime'],
        }),
        'global_run_data': make_n_tup({
            'author': global_runtime_data['caller_user_id'],
            'address': global_runtime_data['caller_contract_id']
        })
    }
