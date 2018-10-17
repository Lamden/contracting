from unittest import TestCase
from seneca.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter
import redis, unittest
r = redis.StrictRedis(host='localhost', port=6379, db=0)

class TestInterface(TestCase):

    def setUp(self):
        r.flushdb()
        self.si = SenecaInterface()
        print('\n\n\n{}:::'.format(self.id))

    def test_import_valid(self):
        self.si.execute_code_str("""
from seneca.test_contracts.sample import good_call
        """)

    def test_execute_invalid(self):
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from seneca.test_contracts.bad import innocent_function
            """)

    def test_import_indirect_invalid_import(self):
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
import seneca.test_contracts.sample
            """)

    def test_import_indirect_invalid_from_import(self):
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from seneca.test_contracts import sample
            """)

    def test_execute_valid(self):
        self.si.execute_code_str("""
from seneca.test_contracts.sample import good_call
good_call()
        """)

    def test_submit_code_str(self):
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
        code_str = """
from seneca.test_contracts.good import one_you_cannot_export
        """
        with self.assertRaises(ImportError) as context:
            self.si.submit_code_str('incorrect', code_str, keep_original=True)

    def test_resubmit_code_str_fail(self):
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
        self.si.execute_code_str("""
from seneca.test_contracts.good import one_you_can_export, one_you_can_also_export, one_you_can_also_also_export
one_you_can_export()
one_you_can_also_export()
one_you_can_also_also_export()
        """)

    def test_scope_fail(self):
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from seneca.test_contracts.good import one_you_cannot_export
            """)

    def test_scope_indirect_fail(self):
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
from seneca.test_contracts.sample import bad_call
bad_call()
            """)


if __name__ == '__main__':
    unittest.main()
