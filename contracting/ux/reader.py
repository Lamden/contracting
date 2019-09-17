from contracting.db.driver import ContractDriver


class Reader:
    def __init__(self, driver=ContractDriver()):
        self.driver = driver

    def get(self, contract, variable, keys):
        pass