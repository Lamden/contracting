from tests.utils import TestExecutor
from seneca.engine.interpreter.utils import ReadOnlyException, CompilationException
import unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'


class TestSubmission(TestExecutor):

    def tearDown(self):
        self.ex.metering = False
        self.reset()

    def test_publish_code_str(self):
        """
            Testing to see if the submission to Ledis works.
        """
        code_str = """
@export
def ok():
    print('i am fine')
        """
        self.ex.publish_code_str('crazy', 'anonymoose', code_str)
        self.ex.execute_code_str("""
from seneca.contracts.crazy import ok

@seed
def init():
    ok()
        """)
        self.assertEqual(code_str, self.ex.get_contract('crazy')['code_str'])

    def test_publish_bad_code(self):
        """
            Trying to import protected functions will fail
        """
        code_str = """
from test_contracts.good import one_you_cannot_export
        """
        with self.assertRaises(ImportError) as context:
            self.ex.publish_code_str('incorrect', 'anonymoose', code_str)

    def test_publish_bad_code_inside_function(self):
        """
            Cannot import protected code inside a function neither.
        """
        code_str = """
def bad_code():
    from test_contracts.good import one_you_cannot_export
        """
        with self.assertRaises(CompilationException) as context:
            self.ex.publish_code_str('incorrect', 'anonymoose', code_str)

    def test_republish_code_str_fail(self):
        """
            Republishting code to the same smart contract name will fail
        """
        self.ex.publish_code_str('crazy', 'anonymoose', """
def ok():
    print('i am fine')
        """)
        with self.assertRaises(Exception) as context:
            self.ex.publish_code_str('crazy', 'anonymoose', """
def fail():
    print('i am not fine')
            """)


if __name__ == '__main__':
    unittest.main()
