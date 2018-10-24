from unittest import TestCase
from seneca.interface.interface import SenecaInterface
import redis, unittest
r = redis.StrictRedis(host='localhost', port=6379, db=0)


class TestInterface(TestCase):

    def setUp(self):
        r.flushdb()
        self.si = SenecaInterface()
        print('\n\n\n{}:::'.format(self.id))

    def test_import_valid(self):
        """
            This is a valid way to import
        """
        self.si.execute_code_str("""
from seneca.test_contracts.sample import good_call, reasonable_call
        """)

    def test_import_invalid(self):
        """
            This is a valid way to import, but you cannot import "importlib"
            and other such libraries. Only ones from the whitelist
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from seneca.test_contracts.bad import innocent_function
            """)

    def test_import_star(self):
        """
            Import * is currently allowed but calling on protected functions
            will still fail
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from seneca.test_contracts.sample import *
secret_call()
            """)

    def test_import_indirect_invalid_import(self):
        """
            You cannot import the entire module. You must import its functions
            seperately. (See TestInterface.test_import_valid())
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
import seneca.test_contracts.sample
            """)

    def test_import_indirect_invalid_from_import(self):
        """
            Just as the previous test case, you cannot import the whole module
            using this syntax neither.
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from seneca.test_contracts import sample
            """)

    def test_execute_valid(self):
        """
            Testing to see if the function can be called.
        """
        self.si.execute_code_str("""
from seneca.test_contracts.sample import good_call
good_call()
        """)

    def test_submit_code_str(self):
        """
            Testing to see if the submission to Redis works.
        """
        code_str = """
@export
def ok():
    print('i am fine')
        """
        self.si.submit_code_str('crazy', code_str, keep_original=True)
        self.si.execute_code_str("""
from seneca.contracts.crazy import ok
ok()
        """)
        self.assertEqual(code_str, self.si.get_code('crazy'))

    def test_submit_bad_code(self):
        """
            Trying to import protected functions will fail
        """
        code_str = """
from seneca.test_contracts.good import one_you_cannot_export
        """
        with self.assertRaises(ImportError) as context:
            self.si.submit_code_str('incorrect', code_str, keep_original=True)

    def test_submit_bad_code_inside_function(self):
        """
            Cannot import protected code inside a function neither.
        """
        code_str = """
def bad_code():
    from seneca.test_contracts.good import one_you_cannot_export
        """
        with self.assertRaises(ImportError) as context:
            self.si.submit_code_str('incorrect', code_str, keep_original=True)

    def test_resubmit_code_str_fail(self):
        """
            Resubmitting code to the same smart contract name will fail
        """
        self.si.submit_code_str('crazy', """
def ok():
    print('i am fine')
        """, keep_original=True)
        with self.assertRaises(Exception) as context:
            self.si.submit_code_str('crazy', """
def fail():
    print('i am not fine')
            """, keep_original=True)

    def test_scope(self):
        """
            Importing exported functions should pass
        """
        self.si.execute_code_str("""
from seneca.test_contracts.good import one_you_can_export, one_you_can_also_export, one_you_can_also_also_export
one_you_can_export()
one_you_can_also_export()
one_you_can_also_also_export()
        """)

    def test_scope_fail(self):
        """
            Importing protected functions should fail
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from seneca.test_contracts.good import one_you_cannot_export
            """)


if __name__ == '__main__':
    unittest.main()
