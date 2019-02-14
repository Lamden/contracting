from tests.utils import captured_output, TestInterface
import redis, unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestGenesis(TestInterface):

    def test_publish_code_str(self):
        pass



if __name__ == '__main__':
    unittest.main()
