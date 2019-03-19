from seneca.engine.interpreter.executor import Executor
from seneca.engine.interpreter.parser import Parser
import types


class LocalInterface(Executor):

    def reset_all_data(self):
        Parser.initialized = False
        default_interface.driver.flushall()
        default_interface.setup_official_contracts()

    def delete_contract(self, name):

        self.driver.hdel('contracts', name)

        for key in self.driver.scan_iter('{}:*'.format(name)):
            self.driver.delete(key)


default_interface = LocalInterface(concurrency=False, metering=False)


class SenecaFunction:
    def __init__(self, driver, contract_name, func_name, default_sender, **kwargs):
        self.contract_name = contract_name
        self.func_name = func_name
        self.kwargs = kwargs
        self.sender = default_sender
        self.driver = driver

    def __call__(self, *args, **kwargs):
        return self.driver.execute_function(
            self.contract_name, self.func_name,
            self.sender,
            kwargs=kwargs
        )


class ContractWrapper:
    def __init__(self, contract_name=None, driver=default_interface, default_sender=None):
        contract = driver.get_contract(contract_name)
        self.driver = driver
        self.author = contract['author']
        self.default_sender = default_sender
        contract_code = contract['code_obj']

        codes = [cd for cd in contract_code.co_consts if isinstance(cd, types.CodeType)]
        for _c in codes:
            func_name, kwargs = _c.co_name, _c.co_varnames
            setattr(self, func_name, SenecaFunction(driver, contract_name, func_name,
                                                    self.default_sender,
                                                    kwargs=kwargs))


def publish_function(f, name, author):
    default_interface.publish_function(f, contract_name=name, author=author)
    return ContractWrapper(contract_name=name, driver=default_interface, default_sender=author)
