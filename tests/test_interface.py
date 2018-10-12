from unittest import TestCase
from seneca.interface import SenecaInterface
import redis, unittest
r = redis.StrictRedis(host='localhost', port=6379, db=0)

class TestInterface(TestCase):

    def setUp(self):
        r.flushdb()
        self.si = SenecaInterface()

    def test_import_valid(self):
        self.si.execute_code_str("""
from seneca.contracts import sample
        """)

    def test_execute_invalid(self):
        with self.assertRaises(Exception) as context:
            self.si.execute_code_str("""
from seneca.contracts import bad
            """)

    def test_execute_valid(self):
        self.si.execute_code_str("""
from seneca.contracts import sample
sample.good_call()
        """)

    def test_submit_code_str(self):
        code_str = """
def ok():
    print('i am fine')
        """
        self.si.submit_code_str('crazy', code_str, keep_original=True)
        self.si.execute_code_str("""
from seneca.contracts import crazy
crazy.ok()
        """)
        self.assertEqual(code_str, self.si.get_code('crazy'))

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
from seneca.contracts import good
good.one_you_can_export()
good.one_you_can_also_export()
good.one_you_can_also_also_export()
        """)

    def test_scope_fail(self):
        with self.assertRaises(Exception) as context:
            self.si.execute_code_str("""
from seneca.contracts import good
good.one_you_cannot_export()
            """)


if __name__ == '__main__':
    unittest.main()
