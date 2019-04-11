from unittest import TestCase
from seneca.db.driver import ContractDriver
from seneca.db.orm import Datum, Variable, Hash

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


class TestHash(TestCase):
    def setUp(self):
        driver.flush()

    def tearDown(self):
        driver.flush()

    def test_set(self):
        contract = 'stustu'
        name = 'balance'
        delimiter = driver.delimiter

        raw_key_1 = '{}{}{}'.format(contract, delimiter, name)
        raw_key_1 += ':stu'

        h = Hash(contract, name, driver=driver)

        h.set('stu', 1234)

        self.assertEqual(driver.get(raw_key_1), 1234)

    def test_get(self):
        contract = 'stustu'
        name = 'balance'
        delimiter = driver.delimiter

        raw_key_1 = '{}{}{}'.format(contract, delimiter, name)
        raw_key_1 += ':stu'

        driver.set(raw_key_1, 1234)

        h = Hash(contract, name, driver=driver)

        self.assertEqual(h.get('stu'), 1234)

    def test_set_get(self):
        contract = 'stustu'
        name = 'balance'

        h = Hash(contract, name, driver=driver)

        h.set('stu', 1234)
        _h = h.get('stu')

        self.assertEqual(_h, 1234)

        h.set('colin', 5678)
        _h2 = h.get('colin')

        self.assertEqual(_h2, 5678)

    def test_setitem(self):
        contract = 'blah'
        name = 'scoob'
        delimiter = driver.delimiter

        h = Hash(contract, name, driver=driver)

        prefix = '{}{}{}{}'.format(contract, delimiter, name, h.delimiter)

        h['stu'] = 9999999

        raw_key = '{}stu'.format(prefix)

        self.assertEqual(driver.get(raw_key), 9999999)

    def test_getitem(self):
        contract = 'blah'
        name = 'scoob'
        delimiter = driver.delimiter

        h = Hash(contract, name, driver=driver)

        prefix = '{}{}{}{}'.format(contract, delimiter, name, h.delimiter)

        raw_key = '{}stu'.format(prefix)

        driver.set(raw_key, 54321)

        self.assertEqual(h['stu'], 54321)