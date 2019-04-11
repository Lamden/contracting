from seneca.db.driver import ContractDriver
from seneca import config


class Variable:
    def __init__(self, contract, name, driver: ContractDriver):
        self.driver = driver
        self.key = self.driver.make_key(contract, name)

    def set(self, value):
        self.driver.set(self.key, value)

    def get(self):
        return self.driver.get(self.key)


class Hash:
    def __init__(self, contract, name, driver: ContractDriver):
        self.driver = driver
        self.key = self.driver.make_key(contract, name)
        self.delimiter = config.RESOURCE_KEY