from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException, CompilationException
from os.path import join
from tests.utils import captured_output, TestInterface
import redis, unittest, seneca


class TestSubmission(TestInterface):
    def test_floats_to_decimals(self):
        code_str = \
'''
f = 123.0000000000001
print(repr(f))
'''

        self.si.execute_code_str(code_str)