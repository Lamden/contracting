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


class Context:
    def __init__(self, upstream_call_stack):
        self.call_stack = upstream_call_stack
        self.contract_address = upstream_call_stack[0][1]
        self.author = upstream_call_stack[0][0]

    def upstream(self):
        return Context(upstream_call_stack=self.call_stack[1:])

    def last(self):
        return Context(upstream_call_stack=list(self.call_stack[-1]))


def make_exports(global_runtime_data):
    this = Context(global_runtime_data['call_stack'][0])
    upstream = this.upstream()
    sender = this.last().author

    return {
        'this': this,
        'upstream': upstream,
        'sender': sender
    }


def run_tests(_):
    '''
    # TODO: Write tests for this module.
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
