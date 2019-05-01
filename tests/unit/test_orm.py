from unittest import TestCase
from contracting.db.driver import ContractDriver
from contracting.db.orm import Datum, Variable, ForeignHash, ForeignVariable, Hash
# from contracting.stdlib.env import gather

# Variable = gather()['Variable']
# Hash = gather()['Hash']
# ForeignVariable = gather()['ForeignVariable']
# ForeignHash = gather()['ForeignHash']

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
        #driver.flush()
        pass

    def test_set(self):
        contract = 'stustu'
        name = 'balance'
        delimiter = driver.delimiter

        raw_key = '{}{}{}'.format(contract, delimiter, name)

        v = Variable(contract, name, driver=driver)
        v.set(1000)

        self.assertEqual(driver.get(raw_key), 1000)

    def test_get(self):
        contract = 'stustu'
        name = 'balance'
        delimiter = driver.delimiter

        raw_key = '{}{}{}'.format(contract, delimiter, name)

        driver.set(raw_key, 1234)

        v = Variable(contract, name, driver=driver)
        _v = v.get()

        self.assertEqual(_v, 1234)

    def test_set_get(self):
        contract = 'stustu'
        name = 'balance'

        v = Variable(contract, name, driver=driver)
        v.set(1000)

        _v = v.get()

        self.assertEqual(_v, 1000)


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

        driver.commit()

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

    def test_setitems(self):
        contract = 'blah'
        name = 'scoob'

        h = Hash(contract, name, driver=driver)
        h['stu'] = 123
        h['stu', 'raghu'] = 1000
        driver.commit()

        val = driver.get('blah.scoob:stu:raghu')
        self.assertEqual(val, 1000)

    def test_setitems_too_many_dimensions_fails(self):
        contract = 'blah'
        name = 'scoob'

        h = Hash(contract, name, driver=driver)

        with self.assertRaises(Exception):
            h['a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c'] = 1000

    def test_setitems_key_too_large(self):
        contract = 'blah'
        name = 'scoob'

        h = Hash(contract, name, driver=driver)

        key = 'a' * 1025

        with self.assertRaises(Exception):
            h[key] = 100

    def test_setitems_keys_too_large(self):
        contract = 'blah'
        name = 'scoob'

        h = Hash(contract, name, driver=driver)

        key1 = 'a' * 800
        key2 = 'b' * 100
        key3 = 'c' * 200

        with self.assertRaises(Exception):
            h[key1, key2, key3] = 100

    def test_getitems_keys(self):
        contract = 'blah'
        name = 'scoob'
        delimiter = driver.delimiter

        h = Hash(contract, name, driver=driver)

        prefix = '{}{}{}{}'.format(contract, delimiter, name, h.delimiter)

        raw_key = '{}stu:raghu'.format(prefix)

        driver.set(raw_key, 54321)

        driver.commit()

        self.assertEqual(h['stu', 'raghu'], 54321)

    def test_getsetitems(self):
        contract = 'blah'
        name = 'scoob'
        delimiter = driver.delimiter

        h = Hash(contract, name, driver=driver)

        h['stu', 'raghu'] = 999

        driver.commit()

        self.assertEqual(h['stu', 'raghu'], 999)

    def test_getitems_keys_too_large(self):
        contract = 'blah'
        name = 'scoob'

        h = Hash(contract, name, driver=driver)

        key1 = 'a' * 800
        key2 = 'b' * 100
        key3 = 'c' * 200

        with self.assertRaises(Exception):
            x = h[key1, key2, key3]

    def test_getitems_too_many_dimensions_fails(self):
        contract = 'blah'
        name = 'scoob'

        h = Hash(contract, name, driver=driver)

        with self.assertRaises(Exception):
            a = h['a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c']

    def test_getitems_key_too_large(self):
        contract = 'blah'
        name = 'scoob'

        h = Hash(contract, name, driver=driver)

        key = 'a' * 1025

        with self.assertRaises(Exception):
            a = h[key]

    def test_getitem_returns_default_value_if_none(self):
        contract = 'blah'
        name = 'scoob'

        h = Hash(contract, name, driver=driver, default_value=0)

        self.assertEqual(h['hello'], 0)

class TestForeignVariable(TestCase):
    def setUp(self):
        driver.flush()

    def tearDown(self):
        driver.flush()

    def test_set(self):
        contract = 'stustu'
        name = 'balance'

        f_contract = 'colinbucks'
        f_name = 'balances'

        f = ForeignVariable(contract, name, f_contract, f_name, driver=driver)

        with self.assertRaises(ReferenceError):
            f.set('poo')

    def test_get(self):
        # set up the foreign variable
        contract = 'stustu'
        name = 'balance'

        f_contract = 'colinbucks'
        f_name = 'balances'

        f = ForeignVariable(contract, name, f_contract, f_name, driver=driver)

        # set the variable using the foreign names (assuming this is another contract namespace)
        v = Variable(f_contract, f_name, driver=driver)
        v.set('howdy')

        self.assertEqual(f.get(), 'howdy')


class TestForeignHash(TestCase):
    def setUp(self):
        driver.flush()

    def tearDown(self):
        #driver.flush()
        pass

    def test_set(self):
        # set up the foreign variable
        contract = 'stustu'
        name = 'balance'

        f_contract = 'colinbucks'
        f_name = 'balances'

        f = ForeignHash(contract, name, f_contract, f_name, driver=driver)

        with self.assertRaises(ReferenceError):
            f.set('stu', 1234)

    def test_get(self):
        # set up the foreign variable
        contract = 'stustu'
        name = 'balance'

        f_contract = 'colinbucks'
        f_name = 'balances'

        f = ForeignHash(contract, name, f_contract, f_name, driver=driver)

        h = Hash(f_contract, f_name, driver=driver)
        h.set('howdy', 555)

        self.assertEqual(f.get('howdy'), 555)

    def test_setitem(self):
        # set up the foreign variable
        contract = 'stustu'
        name = 'balance'

        f_contract = 'colinbucks'
        f_name = 'balances'

        f = ForeignHash(contract, name, f_contract, f_name, driver=driver)

        with self.assertRaises(ReferenceError):
            f['stu'] = 1234

    def test_getitem(self):
        # set up the foreign variable
        contract = 'stustu'
        name = 'balance'

        f_contract = 'colinbucks'
        f_name = 'balances'

        f = ForeignHash(contract, name, f_contract, f_name, driver=driver)

        h = Hash(f_contract, f_name, driver=driver)
        h['howdy'] = 555

        self.assertEqual(f['howdy'], 555)