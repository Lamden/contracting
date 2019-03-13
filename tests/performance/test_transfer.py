from tests.utils import TestExecutor
import unittest, time

CONTRACT_COUNT = 10000


class TestTransfer(TestExecutor):

    def setUp(self):
        super().setUp()
        self.ex.execute_function('currency', 'mint', '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502', kwargs={'to': 'stu', 'amount': CONTRACT_COUNT ** 2})
        self.balances = self.ex.get_resource('currency', 'balances')
        self.print_balance()
        self.start = time.time()

    def tearDown(self):
        elapsed = time.time() - self.start
        print('Finished {} contracts in {}s!'.format(CONTRACT_COUNT, elapsed))
        print('Rate: {}tps'.format(CONTRACT_COUNT / elapsed))
        self.print_balance()

    def print_balance(self):
        self.ex.metering = False
        stu = self.balances['stu']
        ass = self.balances['ass']
        print('stu has a balance of: {}'.format(stu))
        print('ass has a balance of: {}'.format(ass))

    def test_transfer_template_without_metering(self):
        for i in range(CONTRACT_COUNT):
            self.ex.execute_function('currency', 'transfer', 'stu', kwargs={
                'to': 'ass',
                'amount': 1
            })

    def test_transfer_template_with_metering(self):
        self.ex.metering = True
        for i in range(CONTRACT_COUNT):
            self.ex.execute_function('currency', 'transfer', 'stu', 3000, kwargs={
                'to': 'ass',
                'amount': 1
            })

    def test_transfer_template_with_metering_all_fail(self):
        self.ex.metering = True
        for i in range(CONTRACT_COUNT):
            try:
                self.ex.execute_function('currency', 'transfer', 'stu', 100, kwargs={
                    'to': 'ass',
                    'amount': 1
                })
            except Exception as e:
                pass

if __name__ == '__main__':
    unittest.main()
