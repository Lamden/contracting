from seneca.engine.interpret.utils import ReadOnlyException, CompilationException
from tests.utils import TestExecutor
import unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestRedis(TestExecutor):

    def test_read_only_variables(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
__contract__ = 'hacks'
            """)

    def test_read_only_variables_custom(self):
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
bird = 'hacks'
            """, {'bird': '123'})

    def test_read_only_variables_aug_assign(self):
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
bird += 1
            """, {'bird': 123})

    def test_import_datatypes(self):
        self.ex.execute_code_str("""
from seneca.libs.datatypes import hmap
hmap('balance', str, int)
        """)

    def test_import_datatypes_reassign(self):
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
from seneca.libs.datatypes import hmap
hmap = 'hacked'
            """)
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
seed = 'hacked'
            """)

    def test_store_meta(self):
        self.ex.execute_code_str("""
from seneca.libs.datatypes import hmap
@export
def callit(a,b,c=1,d=2):
    return 1,2
some_map = hmap('balance', str, int)
t, r = 2,3
x = 45
        """)

if __name__ == '__main__':
    unittest.main()
