from unittest import TestCase
from unittest.mock import MagicMock
from seneca.engine.client import *
from seneca.engine.interface import SenecaInterface
from seneca.libs.logger import overwrite_logger_level
import time, random


GENESIS_AUTHOR = 'davis'


XFER_CODE_STR = """ \

from seneca.contracts.currency import transfer
transfer('{receiver}', {amount})
"""


MINT_CODE_STR = """ \
from seneca.contracts.currency import mint
mint({}, {})
"""

CONTRACTS_TO_STORE = {'currency': 'currency.sen.py'}
# NUM_WALLETS = 10 ** 5
NUM_WALLETS = 10 ** 2
SEED_AMOUNT = 10 ** 6
PERSON_A = 'conflictor_a'
PERSON_B = 'conflictor_b'


class MockContract:
    def __init__(self, sender: str, code: str, contract_name: str):
        self.sender, self.code, self.contract_name = sender, code, contract_name


def setup():
    # overwrite_logger_level(0)
    with SenecaInterface(False, bypass_currency=True) as interface:
        interface.r.flushall()

        # Store all smart contracts in CONTRACTS_TO_STORE
        import seneca
        test_contracts_path = seneca.__path__[0] + '/../test_contracts/'

        for contract_name, file_name in CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code_str = f.read()
                interface.publish_code_str(contract_name, GENESIS_AUTHOR, code_str)

        start = time.time()
        print("------ MINTING -------")
        print("Minting {} wallets...".format(NUM_WALLETS))
        for i in range(NUM_WALLETS):
            interface.execute_function(module_path='seneca.contracts.currency.mint',
                                       sender=GENESIS_AUTHOR, to=str(i), amount=SEED_AMOUNT, stamps=1000)
        for w in (PERSON_A, PERSON_B):
            interface.execute_function(module_path='seneca.contracts.currency.mint',
                                       sender=GENESIS_AUTHOR, to=w, amount=SEED_AMOUNT, stamps=1000)
        print("Finished minting wallet in {} seconds".format(round(time.time()-start, 2)))
        print("----------------------")


def create_currency_tx(sender: str, receiver: str, amount: int, contract_name: str='currency'):
    code = XFER_CODE_STR.format(receiver=receiver, amount=amount)
    contract = MockContract(sender=sender, code=code, contract_name=contract_name)
    return contract


def test_baseline(num_contracts: int=30000):
    start = time.time()
    print(" ----- BASELINE ------")
    print("Running {} contracts with random addresses...".format(num_contracts))
    with SenecaInterface(False,  bypass_currency=True) as interface:
        for i in range(num_contracts):
            amount = 1
            sender, receiver = random.sample(range(NUM_WALLETS), 2)
            interface.execute_function(module_path='seneca.contracts.currency.transfer',
                                       sender=str(sender), to=str(receiver), amount=amount, stamps=1000)
    dur = time.time()-start
    print("Finished running baseline contracts in {} seconds ".format(round(dur, 2)))
    print("Baseline TPS: {}".format(num_contracts/dur))
    print("----------------------")


def test_cr(num_contracts: int=30000):
    raise NotImplementedError()


if __name__ == '__main__':
    setup()

    # First, we test baseline
    test_baseline()