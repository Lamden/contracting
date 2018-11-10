from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException, CompilationException
from os.path import join
from tests.utils import captured_output, TestInterface
import redis, unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestImports(TestInterface):

    def test_import_valid(self):
        """
            This is a valid way to import
        """
        self.si.execute_code_str("""
from test_contracts.sample import good_call, reasonable_call
        """)

    def test_import_invalid(self):
        """
            This is a valid way to import, but you cannot import "importlib"
            and other such libraries. Only ones from the whitelist
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from test_contracts.bad import innocent_function
            """)

    def test_import_direct_invalid(self):
        """
            This is a valid way to import, but you cannot import "importlib"
            and other such libraries. Only ones from the whitelist
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
import json
            """)

    def test_import_global_variable_invalid(self):
        """
            This is a valid way to import, but you cannot import "importlib"
            and other such libraries. Only ones from the whitelist
        """

        with captured_output() as (out, err):
            with self.assertRaises(CompilationException) as context:
                self.si.execute_code_str("""
from test_contracts.good import balances
print('Hacked', balances) # Should not print this!
                """)
            self.assertEqual(out.getvalue().strip(), '')

    def test_import_star(self):
        """
            Import * is currently not allowed
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from test_contracts.sample import *
            """)

    def test_import_indirect_invalid_import(self):
        """
            You cannot import the entire module. You must import its functions
            seperately. (See TestInterface.test_import_valid())
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
import test_contracts.sample
            """)

    def test_import_indirect_invalid_from_import(self):
        """
            Just as the previous test case, you cannot import the whole module
            using this syntax neither.
        """
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from test_contracts import sample
            """)

    def test_execute_valid(self):
        """
            Testing to see if the function can be called.
        """
        self.si.execute_code_str("""
from test_contracts.sample import good_call
good_call()
        """)

if __name__ == '__main__':
    unittest.main()
