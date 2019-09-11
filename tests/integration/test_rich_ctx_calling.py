from unittest import TestCase
from contracting.client import ContractingClient


def module1():
    @export
    def get_context2():
        return {
            'owner': ctx2.owner,
            'this': ctx2.this,
            'signer': ctx2.signer,
            'caller': ctx2.caller
        }


def all_in_one():
    @export
    def call_me():
        print(rt.ctx2)
        return call_me_again()

    @export
    def call_me_again():
        print(rt.ctx2)
        return call_me_again_again()

    @export
    def call_me_again_again():
        print('inside call_me_again')
        print({
            'owner': ctx2.owner,
            'this': ctx2.this,
            'signer': ctx2.signer,
            'caller': ctx2.caller
        })


def dynamic_import():
    @export
    def called_from_a_far():
        print('CTX2 from dynamic imp: {}'.format(rt.ctx2))
        m = importlib.import_module('all_in_one')
        print({
            'owner': ctx2.owner,
            'this': ctx2.this,
            'signer': ctx2.signer,
            'caller': ctx2.caller
        })
        m.call_me_again_again()

    @export
    def called_from_a_far_stacked():
        m = importlib.import_module('all_in_one')
        return m.call()


class TestRandomsContract(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        self.c.submit(module1)

        self.c.submit(all_in_one)
        self.c.submit(dynamic_import)

    def test_ctx2(self):
        module = self.c.get_contract('module1')
        print(module.get_context2())

    def test_multi_call(self):
        aio = self.c.get_contract('all_in_one')
        print(aio.call_me())

    def test_dynamic_call(self):
        dy = self.c.get_contract('dynamic_import')
        dy.called_from_a_far()