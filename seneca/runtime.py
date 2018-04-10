'''
Note: at least for now, runtime is a special module and is handled differntly by the module loader.
  Why? Currently for development all smart contracts are loaded into the same
    python interpretter instance. This will not be the case in production code,
    the will be isolated in containers. Runtime data is unique for each smart
    contract but since python modules are singletons runtime data would be the
    same for all contracts in execution tree.

'''

# TODO: make sure this is good/safe
def make_n_tup(d):
    return namedtuple('_', ' '.join(d.keys()))(**d)


def make_exports(global_runtime_data, this_contract_runtime_data):
    return make_n_tup({
        'this_contract': make_n_tup({
            'author': this_contract_runtime_data['author'],
            'execution_datetime': this_contract_runtime_data['datetime'],
        }),
        'root_contract': make_n_tup({
            'author': global_runtime_data['user']
        })
    })
