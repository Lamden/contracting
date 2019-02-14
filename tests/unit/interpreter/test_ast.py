from tests.utils import TestExecutor

class TestSubmission(TestExecutor):
    def test_floats_to_decimals(self):
        code_str = \
'''
h = 22
j = 7
s = 1.1 + 2.2
'''

        self.ex.execute_code_str(code_str)

