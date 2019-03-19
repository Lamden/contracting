from seneca.engine.interpreter.utils import ReadOnlyException
from tests.utils import TestExecutor
import unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestImports(TestExecutor):

    def test_import_valid(self):
        """
            This is a valid way to import
        """
        self.ex.execute_code_str("""
from test_contracts.sample import good_call, reasonable_call
        """)

    def test_import_invalid(self):
        """
            This is a valid way to import, but you cannot import "importlib"
            and other such libraries. Only ones from the whitelist
        """
        with self.assertRaises(ImportError) as context:
            self.ex.execute_code_str("""
from test_contracts.bad import innocent_function
            """)

    def test_import_direct_invalid(self):
        """
            This is a valid way to import, but you cannot import "importlib"
            and other such libraries. Only ones from the whitelist
        """
        with self.assertRaises(ImportError) as context:
            self.ex.execute_code_str("""
import json
            """)

    def test_import_star(self):
        """
            Import * is currently not allowed
        """
        with self.assertRaises(ImportError) as context:
            self.ex.execute_code_str("""
from test_contracts.sample import *
            """)

    def test_import_indirect_invalid_import(self):
        """
            You cannot import the entire module. You must import its functions
            seperately. (See TestInterface.test_import_valid())
        """
        with self.assertRaises(ImportError) as context:
            self.ex.execute_code_str("""
import test_contracts.sample
            """)

    def test_import_indirect_invalid_from_import(self):
        """
            Just as the previous test case, you cannot import the whole module
            using this syntax neither.
        """
        with self.assertRaises(ImportError) as context:
            self.ex.execute_code_str("""
from test_contracts import sample
            """)


if __name__ == '__main__':
    unittest.main()
