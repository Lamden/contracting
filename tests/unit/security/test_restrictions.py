from tests.utils import TestExecutor
from seneca.engine.interpret.utils import CompilationException
from seneca.engine.interpret.parser import Parser
import unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestUserDecorators(TestExecutor):

    def test_class(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
class Happy: pass
            """)

    def test_decorators(self):
        res = self.ex.execute_code_str("""
def dec(fn):
    def _dec(*args, **kwargs):
        return fn('ok', *args, **kwargs)
    return _dec

@dec
def good(s1, s2):
    return s1 + s2

print(good('there'))
        """)

    def test_precision(self):
        res = self.ex.execute_code_str("""
from seneca.libs.decimal import Decimal
def good():
    return Decimal("1") - Decimal("0.95")
assert float(good()) == 0.05, 'Not equal'
        """)


class TestGlobalInit(TestExecutor):

    def test_import(self):
        res = self.ex.execute_code_str("""
from seneca.libs.storage.map import Map
z = Map('z')
        """)
        self.assertEqual(repr(Parser.parser_scope['z']), 'Map:__main__:z')

    def test_assign_anything_other_than_datatype_in_global(self):
        with self.assertRaises(CompilationException) as context:
            res = self.ex.execute_code_str("""
a = 2
            """)

    def test_aug_assign_anything_other_than_datatype_in_global(self):
        with self.assertRaises(TypeError) as context:
            res = self.ex.execute_code_str("""
from seneca.libs.storage.map import Map
a = Map('a')
a += 1
            """)


class TestDecorators(TestExecutor):

    def test_func(self):
        with self.assertRaises(CompilationException) as context:
            res = self.ex.execute_code_str("""
from seneca.libs.storage.map import Map

def init():
    b = []
    b += [Map('ok')]
            """)

    def test_seed(self):
        with self.assertRaises(CompilationException) as context:
            res = self.ex.execute_code_str("""
from seneca.libs.storage.map import Map

@seed
def init():
    b = []
    b += [Map('ok')]
            """)

    def test_export(self):
        with self.assertRaises(CompilationException) as context:
            res = self.ex.execute_code_str("""
from seneca.libs.storage.map import Map

@export
def init():
    b = []
    b += [Map('ok')]
            """)

if __name__ == '__main__':
    unittest.main()
