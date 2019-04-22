from ..db.driver import ContractDriver
from ..execution.runtime import rt
from .. import config
from ..execution.compiler import SenecaCompiler
from types import ModuleType
from ..stdlib import env

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
    def __init__(self, contract, name, driver: ContractDriver=rt.driver):
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


class Contract:
    def __init__(self, driver: ContractDriver=rt.driver):
        self.driver = driver

    def submit(self, name, code, author):
        c = SenecaCompiler(module_name=name)

        code_obj = c.compile(code, lint=True)

        ctx = ModuleType('context')

        ctx.caller = rt.ctx[-1]
        ctx.this = name
        ctx.signer = rt.ctx[0]

        scope = env.gather()
        scope.update({'ctx': ctx})

        exec(code_obj, scope)

        if scope.get(config.INIT_FUNC_NAME) is not None:
            scope[config.INIT_FUNC_NAME]()

        self.driver.set_contract(name=name, code=code, author=author, overwrite=False)
