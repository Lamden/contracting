from unittest import TestCase
from contracting.db.driver import ContractDriver
from contracting.execution.executor import Executor


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


class TestMetering(TestCase):
    def setUp(self):
        # Hard load the submission contract
        self.d = ContractDriver()
        self.d.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.d.set_contract(name='submission',
                            code=contract,
                            author='sys')
        self.d.commit()

        # Execute the currency contract with metering disabled
        self.e = Executor()
        self.e.execute(**TEST_SUBMISSION_KWARGS,
                       kwargs=submission_kwargs_for_file('./test_contracts/currency.s.py'), enable_stamps=False)

    def tearDown(self):
        # self.d.flush()
        pass

    def test_simple_execution_deducts_stamps(self):
        prior_balance = self.d.get('currency.balances:stu')

        status, result, stamps = self.e.execute('stu', 'currency', 'transfer', kwargs={'amount': 100, 'to': 'colin'})
        stamps_used = 1000000 - stamps

        new_balance = self.d.get('currency.balances:stu')

        print(stamps_used)

        self.assertEqual(prior_balance - new_balance - 100, stamps_used)

