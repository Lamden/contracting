'''
Note: at least for now, runtime is a special module and is handled differently by the module loader.
  Why? Currently for development all smart contracts are loaded into the same
    python interpretter instance. This will not be the case in production code,
    the will be isolated in containers. Runtime data is unique for each smart
    contract but since python modules are singletons runtime data would be the
    same for all contracts in execution tree.
'''

from seneca.engine.util import auto_set_fields, make_n_tup
'''
sender
sender_contract
call_stack

this_contract.author
this_contract.address

this_contract._call_stack_index

this_contract.upstream_contract().address
this_contract.upstream_contract().author
'''

call_stack = []

class ContactData:
    @auto_set_fields
    def __init__(self, author, address, _call_stack_index):
        pass

    def upstream(self):
        if self._call_stack_index <= 0:
            raise Exception('No upstream contract exists')

        return call_stack[self._call_stack_index - 1]

    def __repr__(self):
        return str(self.__dict__)


def make_exports(global_runtime_data):
    global call_stack
    call_stack = list(map(lambda x: ContactData(x[1][0], x[1][1], x[0]), enumerate(global_runtime_data['call_stack'])))

    return {
        'this_contract': call_stack[-1],
        'sender': call_stack[0].author,
        'call_stack': call_stack
    }

def run_tests(_):
    '''
    >>> from seneca.libs.runtime import *
    >>> x = make_n_tup(make_exports({'call_stack': [('test_author', 'test_contract_addr')]}))
    >>> x.sender
    'test_author'
    >>> x.this_contract.author
    'test_author'
    >>> x.this_contract.address
    'test_contract_addr'
    >>> x.call_stack
    [{'author': 'test_author', 'address': 'test_contract_addr', '_call_stack_index': 0}]
    >>> try:
    ...     x.this_contract.upstream()
    ... except Exception as e:
    ...     print(e)
    No upstream contract exists

    >>> x = make_n_tup(make_exports({'call_stack': [
    ...    ('caller_author', 'caller_contract'),
    ...    ('lib_author','lib_contract')
    ... ]}))
    >>> x.sender
    'caller_author'
    >>> x.this_contract.author
    'lib_author'
    >>> x.this_contract.upstream().author
    'caller_author'
    >>> x.this_contract.upstream().address
    'caller_contract'
    '''
    import doctest, sys
    from collections import namedtuple

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
