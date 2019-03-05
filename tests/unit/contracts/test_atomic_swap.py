from seneca.tooling import *
from seneca.engine.interpreter.parser import Parser
from tests.utils import TestCaseHeader
import seneca, os, json
from seneca.libs.crypto.hashing import hash_data

path = os.path.abspath('{}/../test_contracts'.format(seneca.__path__[0]))
wallet_a = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
wallet_b = 'a103715914a7aae8dd8fddba945ab63a169dfe6e37f79b4a58bcf85bfd681694'
secret = b'12345678'
hashlock = hash_data(secret, 'sha3_256')
expiration = 1800


class TestAtomicSwap(TestCaseHeader):

    def setUp(self):
        super().setUp()

        self.driver = default_interface.driver
        default_interface.reset_all_data()
        for contract in ['tau']:
            with open('{}/{}.sen.py'.format(path, contract)) as f:
                default_interface.publish_code_str(contract, 'falcon', f.read())

        self.tau = ContractWrapper(contract_name='tau', driver=default_interface, default_sender=wallet_a)
        self.currency = ContractWrapper(contract_name='currency', driver=default_interface, default_sender=wallet_a)
        self.atomic_swap_a = ContractWrapper(contract_name='atomic_swap', driver=default_interface, default_sender=wallet_a)
        self.atomic_swap_b = ContractWrapper(contract_name='atomic_swap', driver=default_interface, default_sender=wallet_b)

    def test_redeem(self):
        self.currency.approve(
            spender='atomic_swap',
            amount=100
        )
        self.assertEqual(self.driver.hget('DecimalHash:currency:allowed:{}'.format(wallet_a), 'atomic_swap'), b'100')
        self.atomic_swap_a.initiate(
            initiator=wallet_a,
            participant=wallet_b,
            expiration=expiration,
            hashlock=hashlock,
            token='currency',
            amount=100
        )
        self.assertEqual(self.driver.hget('DecimalHash:currency:allowed:{}'.format(wallet_a), 'atomic_swap'), b'0.0')
        self.assertEqual(self.driver.hget('DecimalHash:currency:balances', 'atomic_swap'), b'100.0')
        self.assertEqual(
            json.loads(self.driver.hget('DictHash:atomic_swap:swaps:{}'.format(wallet_b), hashlock).decode()), {
                'initiator': wallet_a, 'participant': wallet_b,
                'amount': 100, "token": "currency", "expiration": 1800
            })
        self.atomic_swap_b.redeem(
            secret=secret
        )
        self.assertEqual(self.currency.balance_of(wallet_id=wallet_a)['output'], 999900)
        self.assertEqual(self.currency.balance_of(wallet_id=wallet_b)['output'], 1000100)

    def test_refund(self):
        self.currency.approve(
            spender='atomic_swap',
            amount=100
        )
        self.atomic_swap_a.initiate(
            initiator=wallet_a,
            participant=wallet_b,
            expiration=expiration,
            hashlock=hashlock,
            token='currency',
            amount=100
        )
        self.atomic_swap_a.refund(
            participant=wallet_b,
            secret=secret
        )
        self.assertEqual(self.currency.balance_of(wallet_id=wallet_a)['output'], 1000000)
        self.assertEqual(self.currency.balance_of(wallet_id=wallet_b)['output'], 1000000)

