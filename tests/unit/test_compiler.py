# # from unittest import mock
# # from collections import OrderedDict, defaultdict
# # import random, os, marshal
# # import ujson as json
# # from base64 import b64encode
#
# # from seneca.constants.config import SENECA_PATH
# from unittest import TestCase
#
# from seneca.libs.logger import get_logger
# from seneca.libs.logger import overwrite_logger_level, get_logger
# from seneca.unit.interpreter.compiler import SenecaCompiler
#
#
#
# log = get_logger("TestSenecaCompiler")
#
#
# BASIC_CONTRACT = \
# """
# from seneca.libs.storage.datatypes import Hash
#
# bal = Hash('amounts', default_value=0)
#
# @seneca_export
# def get_cur_amount(account):
#     return bal[account]
# """
#
# ADV_CONTRACT = \
# """
# from seneca.libs.storage.datatypes import Hash
#
# bal = Hash('amounts', default_value=0)
# balances = Hash('balances', default_value=0)
#
# @seneca_construct
# def seed():
#     assert True, 'unchanged comment of balances otherwise error'
#     balances['raghu'] = 10000;
#
# @seneca_export
# def get_balances(account):
#     return balances[account]
# """
#
#
# class TestSenecaCompiler(TestCase):
#
#     LOG_LVL = 1
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         if cls.LOG_LVL:
#             overwrite_logger_level(cls.LOG_LVL)
#
#     @classmethod
#     def tearDownClass(cls):
#         if cls.LOG_LVL:
#             overwrite_logger_level(999999)  # re-enable all logging
#         super().tearDownClass()
#
#     def setUp(self):
#         pass
#
#     def test_basic(self):
#         # log.info("precompiled code:\n{}".format(BASIC_CONTRACT))
#         scomp = SenecaCompiler("basic", BASIC_CONTRACT, True)
#         mcode = scomp.compile()
#         self.assertTrue('_zxqqqq_bal' in mcode)
#         self.assertTrue('seneca_export' in mcode)
#         self.assertTrue('_seneca_reset_context' in mcode)
#         self.assertTrue('seneca_construct' not in mcode)
#
#         # log.info("Compiled code:\n{}".format(mcode))
#
#         # self.assertTrue(client.master_db is not None)
#         # self.assertTrue(client.active_db is None)
#
#         # self.assertEqual(len(client.available_dbs), NUM_CACHES)
#
#
#     def test_advanced(self):
#         # log.info("precompiled code:\n{}".format(ADV_CONTRACT))
#         scomp = SenecaCompiler("adv", ADV_CONTRACT, True)
#         mcode = scomp.compile()
#         # log.info("Compiled code:\n{}".format(mcode))
#         self.assertTrue('_zxqqqqqqqqqq_bal' in mcode)
#         self.assertTrue('_zxqqqqqqqqq_balances' in mcode)
#         self.assertTrue('unchanged comment of balances otherwise error' in mcode)
#         self.assertTrue('def get_balances' in mcode)
#         self.assertTrue('seneca_export' in mcode)
#         self.assertTrue('_seneca_reset_context' in mcode)
#         self.assertTrue('seneca_construct' in mcode)
#
#
#         # self.assertTrue(client.master_db is not None)
#         # self.assertTrue(client.active_db is None)
#
#         # self.assertEqual(len(client.available_dbs), NUM_CACHES)
#
#
# if __name__ == "__main__":
#     import unittest
#     unittest.main()
