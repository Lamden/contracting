from unittest import TestCase
from seneca.db.driver import ContractDriver
from seneca.db.orm import Datum, Variable

driver = ContractDriver(db=1)


class TestDatum(TestCase):
    def setUp(self):
        driver.flush()

    def tearDown(self):
        driver.flush()

    def test_init(self):
        d = Datum('stustu', 'test', driver)
        self.assertEqual(d.key, driver.make_key('stustu', 'test'))


class TestVariable(TestCase):
    def setUp(self):
        driver.flush()

    def tearDown(self):
        driver.flush()

    def test_set_get(self):
        contract = 'stustu'
        name = 'balance'
        delimiter = driver.delimiter

        raw_key = '{}{}{}'.format(contract, delimiter, name)

        v = Variable(contract, name, driver=driver)
        v.set(1000)

        _v = v.get()
        raw_v = driver.get(raw_key)

        self.assertEqual(_v, raw_v)

