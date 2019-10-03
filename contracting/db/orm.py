from contracting.db.driver import ContractDriver
from contracting.execution.runtime import rt
from contracting import config

driver = rt.env.get('__Driver') or ContractDriver()

class Datum:
    def __init__(self, contract, name, driver: ContractDriver):
        self._driver = driver
        self._key = self._driver.make_key(contract, name)


class Variable(Datum):
    def __init__(self, contract, name, driver: ContractDriver=driver, t=None):
        self._type = None

        if isinstance(t, type) or None:
            self._type = t

        super().__init__(contract, name, driver=driver)

    def set(self, value):
        if self._type is not None:
            assert isinstance(value, self._type), 'Wrong type passed to variable! Expected {}, got {}.'.format(
                self._type,
                type(value)
            )

        self._driver.set(self._key, value)

    def get(self):
        return self._driver.get(self._key)


class Hash(Datum):
    def __init__(self, contract, name, driver: ContractDriver=driver, default_value=None):
        super().__init__(contract, name, driver=driver)
        self._delimiter = config.DELIMITER
        self._default_value = default_value

    def set(self, key, value):
        self._driver.set('{}{}{}'.format(self._key, self._delimiter, key), value)

    def get(self, item):
        value = self._driver.get('{}{}{}'.format(self._key, self._delimiter, item))

        # Add Python defaultdict behavior for easier smart contracting
        if value is None:
            value = self._default_value

        return value

    def _validate_key(self, key):
        if isinstance(key, tuple):
            assert len(key) <= config.MAX_HASH_DIMENSIONS, 'Too many dimensions ({}) for hash. Max is {}'.format(
                len(key), config.MAX_HASH_DIMENSIONS
            )

            new_key_str = ''
            for k in key:
                assert not isinstance(k, slice), 'Slices prohibited in hashes.'
                new_key_str += '{}{}'.format(k, self._delimiter)

            key = new_key_str[:-len(self._delimiter)]

        assert len(key) <= config.MAX_KEY_SIZE, 'Key is too long ({}). Max is {}.'.format(len(key), config.MAX_KEY_SIZE)
        return key

    def _prefix_for_args(self, args):
        multi = self._validate_key(args)
        prefix = '{}{}'.format(self._key, self._delimiter)
        if multi != '':
            prefix += '{}{}'.format(multi, self._delimiter)

        return prefix

    def all(self, *args):
        prefix = self._prefix_for_args(args)
        return self._driver.values(prefix=prefix)

    def _items(self, *args):
        prefix = self._prefix_for_args(args)
        return self._driver.items(prefix=prefix)

    def clear(self, *args):
        kvs = self._items(*args)
        for k, v in kvs:
            self._driver.delete(k)

    def __setitem__(self, key, value):
        # handle multiple hashes differently
        key = self._validate_key(key)
        self.set(key, value)

    def __getitem__(self, key):
        key = self._validate_key(key)
        return self.get(key)


class ForeignVariable(Variable):
    def __init__(self, contract, name, foreign_contract, foreign_name, driver: ContractDriver=driver):
        super().__init__(contract, name, driver=driver)
        self.foreign_key = self._driver.make_key(foreign_contract, foreign_name)

    def set(self, value):
        raise ReferenceError

    def get(self):
        return self._driver.get(self.foreign_key)


class ForeignHash(Hash):
    def __init__(self, contract, name, foreign_contract, foreign_name, driver: ContractDriver=driver):
        super().__init__(contract, name, driver=driver)
        self.delimiter = config.DELIMITER

        self.foreign_key = self._driver.make_key(foreign_contract, foreign_name)

    def set(self, key, value):
        raise ReferenceError

    def get(self, item):
        return self._driver.get('{}{}{}'.format(self.foreign_key, self.delimiter, item))

    def __setitem__(self, key, value):
        raise ReferenceError

    def __getitem__(self, item):
        return self.get(item)



