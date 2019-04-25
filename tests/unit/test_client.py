from unittest import TestCase
from seneca.client import SenecaClient, abstract_contract_call
from seneca.db.driver import ContractDriver
from seneca.execution.executor import Executor

def submission_kwargs_for_file(f):
    # Get the file name only by splitting off directories
    split = f.split('/')
    split = split[-1]

    # Now split off the .s
    split = split.split('.')
    contract_name = split[0]

    with open(f) as file:
        contract_code = file.read()

    return {
        'name': contract_name,
        'code': contract_code,
    }


TEST_SUBMISSION_KWARGS = {
    'sender': 'stu',
    'contract_name': 'submission',
    'function_name': 'submit_contract'
}


class TestSenecaClient(TestCase):
    def setUp(self):
        self.c = SenecaClient()
        self.c.raw_driver.flush()

        with open('../../seneca/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission',
                            code=contract,
                            author='sys')

        self.c.raw_driver.commit()

    def tearDown(self):
        self.c.raw_driver.flush()

    def test_get_contract(self):
        print(self.c.get_contract('submission'))

    def test_abstract_contract_call(self):
        abstract_contract_call(0, 0, 0, 0, ass=1, bass=2)