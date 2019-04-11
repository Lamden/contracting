from unittest import TestCase
from seneca.db.driver import ContractDriver
from seneca.db.orm import Datum

driver = ContractDriver(db=1)


class TestDatum(TestCase):
    def setUp(self):
        driver.flush()

    def tearDown(self):
        driver.flush()

    def test_init(self):
        d = Datum('stustu', 'test', driver)
        self.assertEqual(d.key, driver.make_key('stustu', 'test'))

