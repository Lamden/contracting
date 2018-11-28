from tests.utils import TestInterface
from seneca.libs.datatypes import hmap

class TestSubmission(TestInterface):
    def test_floats_to_decimals(self):
        code_str = \
'''
h = 22
j = 7
s = 1.1 + 2.2
print(s)
print(h)
print(h / j)
'''

        self.si.execute_code_str(code_str)

    def test_floats_in_datatypes(self):
        code_str = \
'''

'''
