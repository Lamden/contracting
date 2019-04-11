from seneca.db.driver import ContractDriver
from seneca import config


class Datum:
    def __init__(self, contract, name, driver: ContractDriver):
        self.driver = driver
        self.key = self.driver.make_key(contract, name)


class Variable(Datum):
    def __init__(self, contract, name, driver: ContractDriver):
        super().__init__(contract, name, driver=driver)

    def set(self, value):
        self.driver.set(self.key, value)

    def get(self):
        return self.driver.get(self.key)


class Hash(Datum):
    def __init__(self, contract, name, driver: ContractDriver):
        super().__init__(contract, name, driver=driver)
        self.delimiter = config.DELIMITER

    def set(self, key, value):
        self.driver.set('{}{}{}'.format(self.key, self.delimiter, key), value)

    def get(self, item):
        return self.driver.get('{}{}{}'.format(self.key, self.delimiter, item))

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, item):
        return self.get(item)


class ForeignVariable(Variable):
    def __init__(self, contract, name, foreign_contract, foreign_name, driver:ContractDriver):
        super().__init__(contract, name, driver=driver)
        self.foreign_key = self.driver.make_key(foreign_contract, foreign_name)

        self.driver.set(self.key, self.foreign_key)

    def set(self, value):
        raise ReferenceError

    def get(self):
        return self.driver.get(self.foreign_key)
