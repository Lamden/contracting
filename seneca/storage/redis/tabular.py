"""
Seneca's redis tabular provides a SQLesce interface with redis as the storage
backend.

TODOs:
Method chains to support:

* select('wallet_id').where(wallet_id=wallet_id).run())
* update(balance=old_balance + amount_to_add).where(wallet_id=wallet_id).run()
* insert(wallet_id=wallet_id, balance=0)
"""

primary_test_wallet = b' \x01\xe9\x01\xa2,\xa9\x9bjmi\xabx\xd1\\\x83V\xa2\x7f\x16\x9a\xc1\x05\xc8[&\x80\xdf\xd2\xf1\xf1\xb7\xca\x80\xfa['

# XXX: This is a very ugly hack to put off writing this lib until the basic parser/module loader is done.

class Stub(object):
    def __init__(self): # this method creates the class object.
        self.call_stack = []

    def __getattr__(self, name):
        self.call_stack.append(name)
        return self
    def __call__(self, *args, **kwargs):
        self.call_stack.append((args,kwargs))

        if self.call_stack == [
          'select', (('wallet_id',), {}),
          'where', ((), {'wallet_id': primary_test_wallet}),
          'run', ((), {})
        ]:
            return False
        elif self.call_stack == [
          'select', (('wallet_id',), {}),
          'where', ((), {'wallet_id': primary_test_wallet}),
          'run', ((), {}),
          'insert', ((),{'wallet_id': primary_test_wallet, 'balance': 0}),
          'select', (('wallet_id',), {}),
          'where', ((), {'wallet_id': primary_test_wallet}),
          'run', ((), {}),
          'select', (('balance',), {}),
          'where', ((), {'wallet_id': primary_test_wallet}),
          'run', ((), {})]:
            return [5]
        else:
            #print(self.call_stack)
            pass

        return self

stub = Stub()


def create_table(table_name, column_spec):
    return stub


def get_table(table_name):
    return stub


def column(*args, **kwargs):
    pass
