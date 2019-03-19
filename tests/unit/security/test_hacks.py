from tests.utils import TestExecutor
from seneca.engine.interpreter.utils import ReadOnlyException, CompilationException
import unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'


class TestBasicHacks(TestExecutor):

    def test_read_only_variables(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
__contract__ = 'hacks'
                """)

    def test_import_datatypes(self):
        self.ex.execute_code_str("""
from seneca.libs.storage.datatypes import Hash
Hash('balance')
            """)

    def test_import_datatypes_reassign(self):
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
from seneca.libs.storage.datatypes import Hash

@seed
def init():
    Hash = 'hacked'
                """)

    def test_import_builtin_reassign(self):
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
seed = 'hacked'
                """)

    def test_declare_within_func(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
from seneca.libs.storage.datatypes import Hash
    
@seed
def init():
    some_map = Hash('balance')
                """)


class TestMoreHacks(TestExecutor):

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

@seed
def init():
    good_call = bad_call
    print(good_call())

            """)

    def test_del_variables(self):
        with self.assertRaises(CompilationException) as context:
            self.ex.execute_code_str("""
from test_contracts.sample import good_call

@seed
def init():
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
    
@seed
def init():
    recurse()
            """)

    def test_injection(self):
        self.ex.execute_code_str("""
from seneca.libs.storage.datatypes import Hash

x = Hash('\b\b\b\b\b\b\b\b\b\b\b\b\bHSET DecimalHash:currency:balances hacked 10000')

@seed
def init():
    x['y'] = 2
                    """)
        self.assertEqual(self.ex.driver.hget('DecimalHash:currency:balances', 'hacked'), None)

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
