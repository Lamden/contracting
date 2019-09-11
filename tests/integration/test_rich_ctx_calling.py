from unittest import TestCase
from contracting.client import ContractingClient

def module1():
    import module2
    import module3

    @export
    def get_context():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }

def module2():
    import module4
    import module5

    @export
    def get_context():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }

def module3():
    import module6
    import module7

    @export
    def get_context():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }

def module4():
    @export
    def get_context():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }

def module5():
    import module8

    @export
    def get_context():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }

def module6():
    @export
    def get_context():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }

def module7():
    @export
    def get_context():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }

def module8():
    @export
    def get_context():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }


def all_in_one():
    @export
    def call_me():
        return call_me_again()

    @export
    def call_me_again():
        return call_me_again_again()

    @export
    def call_me_again_again():
        return {
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller
        }

def dynamic_import():
    @export
    def called_from_a_far():
        m = importlib.import_module('all_in_one')
        return m.call_me_again_again()

    @export
    def called_from_a_far_stacked():
        m = importlib.import_module('all_in_one')
        return m.call()

class TestRandomsContract(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        self.c.submit(module8)
        self.c.submit(module7)
        self.c.submit(module6)
        self.c.submit(module5)
        self.c.submit(module4)
        self.c.submit(module3)
        self.c.submit(module2)
        self.c.submit(module1)

        self.c.submit(all_in_one)
        self.c.submit(dynamic_import)

    def test_init(self):
        pass