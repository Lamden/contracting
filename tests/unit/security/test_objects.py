from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException, CompilationException
from os.path import join
from tests.utils import captured_output, TestInterface
import redis, unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestObjects(TestInterface):

    def test_class(self):
        with self.assertRaises(AssertionError) as context:
            self.si.execute_code_str("""
class Happy: pass
            """)

    def test_decorators(self):
        res = self.si.execute_code_str("""
def dec(fn):
    def _dec(*args, **kwargs):
        return fn('ok', *args, **kwargs)
    return _dec

@dec
def good(s1, s2):
    return s1 + s2

print(good('there'))
        """)

    def test_decorators(self):
        res = self.si.execute_code_str("""
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
        res = self.si.execute_code_str("""
from seneca.libs.decimal import Decimal
def good():
    return Decimal("1") - Decimal("0.95")
assert good() == 0.05, 'Not equal'
        """)

if __name__ == '__main__':
    unittest.main()
