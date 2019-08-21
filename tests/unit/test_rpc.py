from unittest import TestCase
from contracting.server import rpc


class TestRPC(TestCase):
    def setUp(self):
        #rpc.driver.set
        pass

    def test_get_contract(self):
        contract = '''
def stu():
    print('howdy partner')
'''

        name = 'stustu'
        author = 'woohoo'
        _t = 'test'

        rpc.driver.set_contract(name, contract, author=author, _type=_t)

        response = rpc.get_contract('stustu')

        self.assertEqual(response, contract)

    def test_get_methods(self):
        contract = '''
def stu():
    print('howdy partner')
'''

        name = 'stustu'
        author = 'woohoo'
        _t = 'test'

        rpc.driver.set_contract(name, contract, author=author, _type=_t)

        response = rpc.get_methods('stustu')

        expected = [{'name': 'stu', 'arguments': []}]

        self.assertEqual(response, expected)