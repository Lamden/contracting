from tests.utils import TestExecutor
from seneca.engine.interpret.utils import CompilationException
import unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestObjects(TestExecutor):

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

if __name__ == '__main__':
    unittest.main()
