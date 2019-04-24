from ..db.driver import ContractDriver
from ..execution.runtime import rt
from .. import config


class Datum:
    def __init__(self, contract, name, driver: ContractDriver):
        self.driver = driver
        self.key = self.driver.make_key(contract, name)


class Variable(Datum):
    def __init__(self, contract, name, driver: ContractDriver=rt.driver):
        super().__init__(contract, name, driver=driver)

    def set(self, value):
        self.driver.set(self.key, value)

    def get(self):
        return self.driver.get(self.key)


class Hash(Datum):
    def __init__(self, contract, name, driver: ContractDriver=rt.driver, default_value=None):
        super().__init__(contract, name, driver=driver)
        self.delimiter = config.DELIMITER
        self.default_value = default_value

    def set(self, key, value):
        self.driver.set('{}{}{}'.format(self.key, self.delimiter, key), value)

    def get(self, item):
        value = self.driver.get('{}{}{}'.format(self.key, self.delimiter, item))

        # Add Python defaultdict behavior for easier smart contracting
        if value is None:
            value = self.default_value

        return value

    def _validate_key(self, key):
        if isinstance(key, tuple):
            assert len(key) <= config.MAX_HASH_DIMENSIONS, 'Too many dimensions ({}) for hash. Max is {}'.format(
                len(key), config.MAX_HASH_DIMENSIONS
            )

            new_key_str = ''
            for k in key:
                assert not isinstance(k, slice), 'Slices prohibited in hashes.'
                new_key_str += '{}{}'.format(k, self.delimiter)

            key = new_key_str[:-len(self.delimiter)]

        assert len(key) <= config.MAX_KEY_SIZE, 'Key is too long ({}). Max is {}.'.format(len(key), config.MAX_KEY_SIZE)
        return key

    def __setitem__(self, key, value):
        # handle multiple hashes differently
        key = self._validate_key(key)
        self.set(key, value)

    def __getitem__(self, key):
        key = self._validate_key(key)
        return self.get(key)


class ForeignVariable(Variable):
    def __init__(self, contract, name, foreign_contract, foreign_name, driver: ContractDriver=rt.driver):
        super().__init__(contract, name, driver=driver)
        self.foreign_key = self.driver.make_key(foreign_contract, foreign_name)

        self.driver.set(self.key, self.foreign_key)

    def set(self, value):
        raise ReferenceError

    def get(self):
        return self.driver.get(self.foreign_key)


class ForeignHash(Hash):
    def __init__(self, contract, name, foreign_contract, foreign_name, driver: ContractDriver=rt.driver):
        super().__init__(contract, name, driver=driver)
        self.delimiter = config.DELIMITER

        self.foreign_key = self.driver.make_key(foreign_contract, foreign_name)

    def set(self, key, value):
        raise ReferenceError

    def get(self, item):
        return self.driver.get('{}{}{}'.format(self.foreign_key, self.delimiter, item))

    def __setitem__(self, key, value):
        raise ReferenceError

    def __getitem__(self, item):
        return self.get(item)



