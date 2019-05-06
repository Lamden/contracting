from contracting.client import ContractingClient
from unittest import TestCase


def contract():
    storage = Hash()

    @export
    def create(x, y, color):
        storage[x, y] = {
            'color': color,
            'owner': ctx.caller
        }

    @export
    def update(x, y, color):
        s = storage[x, y]

        s['color'] = color

        storage[x, y] = s


class TestComplexStorage(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        self.c.submit(contract)
        self.contract = self.c.get_contract('contract')

    def tearDown(self):
        self.c.flush()

    def test_storage(self):
        self.contract.create(x=1, y=2, color='howdy')
        self.assertEqual(self.contract.storage[1, 2]['color'], 'howdy')

    def test_modify(self):
        self.contract.create(x=1, y=2, color='howdy')
        self.contract.update(x=1, y=2, color='yoyoyo')

        print(self.contract.storage[1, 2])