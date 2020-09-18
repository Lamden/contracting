from unittest import TestCase
from contracting.client import ContractingClient


class TestClient(TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()

    def tearDown(self):
        self.client.flush()

    def test_set_submission_updates_contract_file(self):
        submission_1_code = self.client.raw_driver.get('submission.__code__')

        self.client.flush()
        self.client.set_submission_contract(filename='./precompiled/updated_submission.py')

        submission_2_code = self.client.raw_driver.get('submission.__code__')

        self.assertNotEqual(submission_1_code, submission_2_code)
