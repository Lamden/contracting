from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient


class TestMiscContracts(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract,)

        self.c.raw_driver.commit()

        submission = self.c.get_contract('submission')

        # submit erc20 clone
        with open('./test_contracts/thing.s.py') as f:
            code = f.read()
            self.c.submit(code, name='thing')

        with open('./test_contracts/foreign_thing.s.py') as f:
            code = f.read()
            self.c.submit(code, name='foreign_thing')

        self.thing = self.c.get_contract('thing')
        self.foreign_thing = self.c.get_contract('foreign_thing')

    def test_H_values_return(self):
        output = self.foreign_thing.read_H_hello()
        self.assertEqual(output, 'there')

        output = self.foreign_thing.read_H_something()
        self.assertEqual(output, 'else')

    def test_cant_modify_H(self):
        with self.assertRaises(ReferenceError):
            self.foreign_thing.set_H(k='hello', v='not_there')

    def test_cant_add_H(self):
        with self.assertRaises(ReferenceError):
            self.foreign_thing.set_H(k='asdf', v='123')

    def test_cant_set_V(self):
        with self.assertRaises(ReferenceError):
            self.foreign_thing.set_V(v=123)

    def test_V_returns(self):
        output = self.foreign_thing.read_V()
        self.assertEqual(output, 'hi')


class TestPassHash(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract,)

        self.c.raw_driver.commit()

        submission = self.c.get_contract('submission')

        # submit erc20 clone
        with open('./test_contracts/pass_hash.s.py') as f:
            code = f.read()
            self.c.submit(code, name='pass_hash')

        with open('./test_contracts/test_pass_hash.s.py') as f:
            code = f.read()
            self.c.submit(code, name='test_pass_hash')

        self.pass_hash = self.c.get_contract('pass_hash')
        self.test_pass_hash = self.c.get_contract('test_pass_hash')

    def test_store_value(self):
        self.test_pass_hash.store(k='thing', v='value')
        output = self.test_pass_hash.get(k='thing')

        self.assertEqual(output, 'value')
