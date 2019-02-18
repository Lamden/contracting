from tests.utils import TestExecutor
from seneca.engine.interpret.utils import ReadOnlyException, CompilationException
from os.path import join
from tests.utils import captured_output, TestInterface
import redis, unittest, seneca
from unittest.mock import MagicMock, patch

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestHacks(TestExecutor):

    def test_forbidden_import(self):
        with self.assertRaises(ImportError) as context:
            self.ex.execute_code_str("""
import sys
            """)

    def test_modify_imports(self):
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
from test_contracts.sample import good_call
def bad_call():
    return 'hacked'
good_call = bad_call
            """)

    def test_del_variables(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
from test_contracts.sample import good_call
del good_call
            """)

    def test_access_underscore_attributes(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
v = abs.__self__.__dict__
            """)

    def test_callable_exec(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
callable.__self__.__dict__['exec']('''
import sys
''')
            """)

    def test_globals(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
v = __builtins__['__import__']('sys')
            """)

    def test_tracer(self):
        from seneca.libs.metering.tracer import Tracer
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
__tracer__.set_stamp(1000)
            """, scope={'__tracer__': Tracer()})

    def test_import(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
__import__('sys')
            """)

    def test_recursion(self):
        with self.assertRaises(RecursionError) as context:
            self.ex.execute_code_str("""
def recurse():
    return recurse()
recurse()
            """)

#     def test_overflow(self):
#         with self.assertRaises(ValueError) as context:
#             self.ex.execute_code_str("""
# obj = {}
# for i in range(int(1000000)):
#     obj[i*int(10000000)] = i*int(10000000)
#             """)
#         print('passed through 1st time')
#         with self.assertRaises(ValueError) as context:
#             self.ex.execute_code_str("""
# obj = {}
# for i in range(int(1000000)):
#     obj[i*int(10000000)] = i*int(10000000)
#             """)
#         print('passed through 2nd time')
#
#
#     @patch("seneca.constants.config.CPU_TIME_LIMIT", 3)
#     def test_run_time(self):
#         with self.assertRaises(Exception) as context:
#             self.ex.execute_code_str("""
# for i in range(int(100000000)):
#     a = 1
#             """)


if __name__ == '__main__':
    unittest.main()
