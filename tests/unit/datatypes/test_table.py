from seneca.libs.storage.datatypes import Hash
from seneca.libs.storage.table import Table, Property
from tests.utils import TestDataTypes


class TestTable(TestDataTypes):

    def test_hash_nested_different_type(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True),
            'purpose': str,
        })
        tau = Coin.add_row('tau', 'something')
        balances = Hash('balances')
        balances['hr']['hey'] = tau
        self.assertEqual(balances['hr']['hey'].schema, Coin.schema)
        self.assertEqual(balances['hr']['hey'].data.name, 'tau')
        self.assertEqual(balances['hr']['hey'].data.purpose, 'something')

    def test_table_append(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True),
            'purpose': str,
            'price': int
        })
        Coin.add_row('tau', purpose='anarchy net')
        Coin.add_row(purpose='anarchy net', name='stubucks', price=1)
        Coin.add_row('falcoin', 'anarchy net')

        self.assertEqual(Coin.count, 3)

    def test_table_invalid_property_name(self):
        Coin = Table('Coin', {
            'data': Property(str, required=True)
        })
        tau = Coin.add_row(data='anarchy net')
        self.assertEqual(tau.data.data, 'anarchy net')

    def test_table_indexed(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True, indexed=True),
            'purpose': str,
            'price': int
        })
        Coin.add_row('faltau', purpose='anarchy net')
        Coin.add_row(purpose='anarchy net', name='stubucks', price=1)
        Coin.add_row('falcoin', 'anarchy net')

        self.assertEqual(Coin.find({'$property': 'name', '$exactly': 'faltau'}), [['faltau', 'anarchy net', 0.0]])
        # self.assertEqual(sorted(Coin.find({'$property': 'name', '$matches': 'fal*'})), sorted([['faltau', 'anarchy net', 0.0], ['falcoin', 'anarchy net', 0.0]]))

    def test_table_with_table_as_type(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True),
            'purpose': Property(str, default='anarchy net')
        })
        Company = Table('Company', {
            'name': str,
            'coin': Coin,
            'evaluation': int
        })
        tau = Coin.add_row('tau')
        lamden = Company.add_row('lamden', coin=tau, evaluation=0)
        self.assertEqual(repr(tau), 'Table:test_table_with_table_as_type:Coin')
        self.assertEqual(repr(lamden), 'Table:test_table_with_table_as_type:Company')

    def test_table_with_invalid_table_type(self):
        Coin = Table('Coin', {
            'name': Property(str, True),
            'purpose': Property(str, False, '')
        })
        Fake = Table('Fake', {
            'name': Property(str, True),
            'purpose': Property(str, False, '')
        })
        Company = Table('Company', {
            'name': Property(str),
            'coin': Property(Coin),
            'evaluation': Property(int)
        })
        fake_tau = Fake.add_row('tau', 'anarchy net')
        with self.assertRaises(AssertionError) as context:
            lamden = Company.add_row('lamden', coin=fake_tau, evaluation=0)

    # TODO: Deletion currently not supported by CR
    # def test_table_delete(self):
    #     Coin = Table('Coin', {
    #         'name': Property(str, required=True, indexed=True),
    #         'purpose': str,
    #         'price': int
    #     })
    #     Coin.add_row('faltau', purpose='anarchy net')
    #     Coin.add_row(purpose='anarchy net', name='stubucks', price=1)
    #     Coin.add_row('falcoin', 'anarchy net')
    #     Coin.delete_table()
    #     for item in self.ex.driver.keys():
    #         self.assertFalse(item.decode().startswith(Coin.key))
    #
    # def test_delete_row(self):
    #     Coin = Table('Coin', {
    #         'name': Property(str, required=True, indexed=True),
    #         'purpose': str,
    #         'price': int
    #     })
    #     Coin.add_row('faltau', purpose='anarchy net', price=6)
    #     Coin.add_row(purpose='anarchy net', name='stubucks', price=1)
    #     Coin.add_row('falcoin', 'anarchy net', price=5)
    #     Coin.add_row('falcore', 'anarchy net', price=4)
    #     Coin.add_row('falcone', 'anarchy net', price=41)
    #     Coin.delete({'$property': 'name', '$matches': 'falco*'})
    #     self.assertEqual(Coin.count, 2)

    def test_update_row(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True, indexed=True),
            'purpose': str,
            'price': int
        })
        Coin.add_row('faltau', purpose='anarchy net', price=6)
        Coin.update({'$property': 'name', '$exactly': 'faltau'}, {
            'price': 12
        })
        self.assertEqual(Coin.find({'$property': 'name', '$exactly': 'faltau'}), [['faltau', 'anarchy net', 12]])

    # TODO: Sorting currently not supported
    # def test_table_with_sorted_column(self):
    #     Coin = Table('Coin', {
    #         'name': Property(str, primary_key=True),
    #         'purpose': str,
    #         'price': Property(int, sort=True)
    #     })
    #     Coin.add_row('faltau', purpose='anarchy net', price=6)
    #     Coin.add_row(purpose='anarchy net', name='stubucks', price=10)
    #     Coin.add_row('falcoin', 'anarchy net', price=100)