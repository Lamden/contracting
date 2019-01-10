from seneca.engine.interface import SenecaInterface
import types


class LocalInterface(SenecaInterface):
    def __init__(self, concurrent_mode=False,
                       port=6379,
                       password='',
                       bypass_currency=True):

        super().__init__(concurrent_mode=concurrent_mode,
                         port=port,
                         password=password,
                         bypass_currency=bypass_currency)

    def delete_contract(self, name):
        self.r.hdel('contracts', name)
        self.r.hdel('contracts_code', name)
        self.r.hdel('contracts_meta', name)

        for key in self.r.scan_iter('{}:*'.format(name)):
            self.r.delete(key)


default_driver = LocalInterface(concurrent_mode=False,
                                port=6379,
                                password='',
                                bypass_currency=True)


class SenecaFunction:
    def __init__(self, name, module_path, kwargs, default_sender, driver):
        self.name = name
        self.module_path = module_path
        self.kwargs = kwargs
        self.defaults = {
            'sender': default_sender
        }
        self.driver = driver

    def __call__(self, *args, **kwargs):

        def default(d, k):
            return d if kwargs.get(k) is None else kwargs.get(k)

        sender = self.defaults.get('sender')
        if 'sender' in kwargs.keys():
            sender = kwargs['sender']
            kwargs.pop('sender', None)

        stamps = default(None, 'stamps')

        kwargs['stamps'] = stamps
        kwargs['sender'] = sender

        r = self.driver.execute_function(
            module_path=self.module_path,
            **kwargs
        )

        return r


class ContractWrapper:
    def __init__(self, contract_name=None, driver=default_driver, default_sender=None):
        self.driver = driver
        self.author = driver.get_contract_meta(contract_name)['author']
        self.default_sender = default_sender
        contract_code = driver.get_code_obj(contract_name)

        codes = [cd for cd in contract_code.co_consts if type(cd) == types.CodeType]
        for _c in codes:
            name = _c.co_name
            module_path = 'seneca.contracts.{}.{}'.format(contract_name, _c.co_name)
            kwargs = _c.co_varnames
            setattr(self, name, SenecaFunction(name=name,
                                               module_path=module_path,
                                               kwargs=kwargs,
                                               default_sender=self.default_sender,
                                               driver=self.driver))


def publish_function(f, name, author):
    default_driver.publish_function(f, contract_name=name, author=author)
    return ContractWrapper(contract_name=name, driver=default_driver, default_sender=author)


def export(*args):
    pass
