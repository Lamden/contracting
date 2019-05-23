from ..db.driver import ContractDriver
from ..execution.runtime import rt
from .. import config

driver = rt.env.get('__Driver') or ContractDriver()

class Datum:
    def __init__(self, contract, name, driver: ContractDriver):
        self._driver = driver
        self._key = self._driver.make_key(contract, name)


class Variable(Datum):
    def __init__(self, contract, name, driver: ContractDriver=driver):
        super().__init__(contract, name, driver=driver)

    def set(self, value):
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

    def all(self):
        return self._driver.iter(prefix='{}{}'.format(self._key, self._delimiter))

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

    def all(self):
        return self._driver.iter(prefix='{}{}'.format(self.foreign_key, self.delimiter))

    def __setitem__(self, key, value):
        raise ReferenceError

    def __getitem__(self, item):
        return self.get(item)



