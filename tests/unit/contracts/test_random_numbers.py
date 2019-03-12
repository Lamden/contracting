# from tests.utils import TestExecutor
# import seneca, os
# from seneca.engine.book_keeper import BookKeeper
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
# test_contracts_path = os.path.dirname(seneca.__path__[0]) + '/test_contracts/'
#
#
# class TestRandomNumbers(TestExecutor):
#     CONTRACTS_TO_STORE = {'random_nums': 'random_nums_test.sen.py',
#                           'importing_randoms': 'importing_randoms.sen.py'}
#
#     def setUp(self):
#         self.flush()
#         context = {
#             'sbb_idx': None,
#             'contract_idx': None,
#             'data': None,
#             'last_block_hash': b'abc'
#         }
#         BookKeeper.set_cr_info(**context)
#         for contract_name, file_name in self.CONTRACTS_TO_STORE.items():
#             with open(test_contracts_path + file_name) as f:
#                 code_str = f.read()
#                 self.ex.publish_code_str(contract_name, GENESIS_AUTHOR, code_str)
#
#     def test_shuffle_cards(self):
#
#         f = self.ex.execute_function(
#             'random_nums', 'shuffle_cards',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#         )
#
#         f2 = self.ex.execute_function(
#             'random_nums', 'shuffle_cards',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#         )
#
#         self.assertEqual(f['output'], f2['output'])
#
#     def test_random_num_imports(self):
#
#         f = self.ex.execute_function(
#             'importing_randoms', 'yo',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#         )
#
#     def test_random_num_one_vs_two(self):
#
#         f = self.ex.execute_function(
#             'random_nums', 'random_number',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#             kwargs={
#                 'k': 1000
#             }
#         )
#
#         f2 = self.ex.execute_function(
#             'random_nums', 'random_number_2',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#             kwargs={
#                 'k': 1000
#             }
#         )
#         self.assertEqual(f['output'], 790)
#         self.assertEqual(f2['output'], 220)
#
#     def test_random_getrandbits(self):
#
#         f = self.ex.execute_function(
#             'random_nums', 'random_bits',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#             kwargs={
#                 'k': 20
#             }
#         )
#
#         self.assertEqual(f['output'], 386311)
#
#     def test_random_range_int(self):
#
#         f = self.ex.execute_function(
#             'random_nums', 'int_in_range',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#             kwargs={
#                 'a': 100,
#                 'b': 5000
#             }
#         )
#
#         f2 = self.ex.execute_function(
#             'random_nums', 'int_in_range',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#             kwargs={
#                 'a': 100,
#                 'b': 50000
#             }
#         )
#
#         self.assertEqual(f['output'], 2334)
#         self.assertEqual(f2['output'], 22879)
#
#     def test_random_choice(self):
#
#         f = self.ex.execute_function(
#             'random_nums', 'pick_cities',
#             sender=GENESIS_AUTHOR,
#             stamps=None,
#             kwargs={
#                 'k': 2
#             }
#         )
#
#         self.assertEqual(f['output'], ['New York', 'Chicago'])
