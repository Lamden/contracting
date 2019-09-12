from unittest import TestCase
from contracting.client import ContractingClient


class TestElectionHouse(TestCase):
    def setUp(self):
        self.client = ContractingClient()

    def tearDown(self):
        self.client.flush()

    def test_init(self):
        pass