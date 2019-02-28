# from unittest import TestCase
# from unittest.mock import MagicMock
# from seneca.engine.client import *
# from seneca.engine.interface import SenecaInterface
# from decimal import *
#
# GENESIS_AUTHOR = 'davis'
# STAMP_AMOUNT = None
# MINT_WALLETS = {
#     'davis': 10000,
#     'stu': 69,
#     'birb': 8000,
#     'ghu': 9000,
#     'tj': 8000,
#     'ethan': 8000
# }
#
#
# class TestStuCannotNameTestsIfHisLifeDependedOnIt(TestCase):
#     CONTRACTS_TO_STORE = {'decimal_test': 'decimal_test.sen.py', 'currency': 'currency.sen.py'}
#
#     def setUp(self):
#         # overwrite_logger_level(0)
#         with SenecaInterface(False, bypass_currency=True) as interface:
#             interface.r.flushall()
#             # Store all smart contracts in CONTRACTS_TO_STORE
#             import seneca
#             test_contracts_path = seneca.__path__[0] + '/../test_contracts/'
#
#             for contract_name, file_name in self.CONTRACTS_TO_STORE.items():
#                 with open(test_contracts_path + file_name) as f:
#                     code_str = f.read()
#                     interface.publish_code_str(contract_name, GENESIS_AUTHOR, code_str)
#
#             rt = {
#                 'author': GENESIS_AUTHOR,
#                 'sender': GENESIS_AUTHOR,
#                 'contract': 'minter'
#             }
#
#     def test_store_float(self):
#         with SenecaInterface(False, bypass_currency=True) as interface:
#             interface.execute_function(
#                 module_path='seneca.contracts.decimal_test.store_float',
#                 sender=GENESIS_AUTHOR,
#                 stamps=None,
#                 s='floaty',
#                 f=Decimal('0.01')
#             )
#
#             f = interface.execute_function(
#                 module_path='seneca.contracts.decimal_test.read_float',
#                 sender=GENESIS_AUTHOR,
#                 stamps=None,
#                 s='floaty'
#             )
#
#         self.assertEqual(f['output'], Decimal('0.01'))
#
#     def test_add_floats(self):
#         with SenecaInterface(False, bypass_currency=True) as interface:
#             interface.execute_function(
#                 module_path='seneca.contracts.decimal_test.store_float',
#                 sender=GENESIS_AUTHOR,
#                 stamps=None,
#                 s='floaty',
#                 f=Decimal('1.1')
#             )
#
#             interface.execute_function(
#                 module_path='seneca.contracts.decimal_test.store_float',
#                 sender=GENESIS_AUTHOR,
#                 stamps=None,
#                 s='floaty2',
#                 f=Decimal('2.2')
#             )
#
#             f = interface.execute_function(
#                 module_path='seneca.contracts.decimal_test.add_floats',
#                 sender=GENESIS_AUTHOR,
#                 stamps=None,
#                 s1='floaty',
#                 s2='floaty2'
#             )
#
#         self.assertEqual(f['output'], Decimal('3.3'))
#
#     def test_divide_float(self):
#         with SenecaInterface(False, bypass_currency=True) as interface:
#             interface.execute_function(
#                 module_path='seneca.contracts.decimal_test.store_float',
#                 sender=GENESIS_AUTHOR,
#                 stamps=None,
#                 s='floaty',
#                 f=Decimal('3')
#             )
#
#             f = interface.execute_function(
#                 module_path='seneca.contracts.decimal_test.divide_float',
#                 sender=GENESIS_AUTHOR,
#                 stamps=None,
#                 s='floaty',
#             )
#
#         self.assertEqual(f['output'], Decimal('1.5'))
