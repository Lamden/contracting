from unittest import TestCase
from contracting.client import ContractingClient


def multihash_test():
    h = Hash()

    @construct
    def seed():
        for i in range(1000):
            h[i, i+1] = i*2

    @export
    def get():
        return h.all()


class TestElectionHouse(TestCase):
    def setUp(self):
        self.client = ContractingClient()

    def tearDown(self):
        #self.client.flush()
        pass

    def test_multihash_get(self):
        self.client.submit(multihash_test)

        multihash = self.client.get_contract('multihash_test')

        print(multihash.get())