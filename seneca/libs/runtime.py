'''
Note: at least for now, runtime is a special module and is handled differently by the module loader.
  Why? Currently for development all smart contracts are loaded into the same
    python interpretter instance. This will not be the case in production code,
    the will be isolated in containers. Runtime data is unique for each smart
    contract but since python modules are singletons runtime data would be the
    same for all contracts in execution tree.
'''


class Context:
    def __init__(self, upstream_call_stack):
        self.call_stack = upstream_call_stack
        self.contract_address = upstream_call_stack[0][1]
        self.author = upstream_call_stack[0][0]

    def upstream(self):
        if len(self.call_stack) == 1:
            return None
        return Context(upstream_call_stack=self.call_stack[1:])

    def last(self):
        if len(self.call_stack) <= 1:
            return None
        return Context(upstream_call_stack=self.call_stack[-1:])


def make_exports(global_runtime_data):
    this = Context(global_runtime_data['call_stack'])
    return this
    #upstream = this.upstream()
    #sender = this.last().author

    return {
        'this': this,
        'upstream': upstream,
        'sender': sender
    }


def run_tests(_):
    '''
    >>> c = {'call_stack': [('big', 'ol'), ('doinks', 'amish')]}
    >>> x = make_exports(c)
    >>> x.last().author
    'doinks'
    >>> x.last().contract_address
    'amish'
    >>> x.author
    'big'
    >>> x.contract_address
    'ol'
    >>> x.call_stack
    [('big', 'ol'), ('doinks', 'amish')]
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
