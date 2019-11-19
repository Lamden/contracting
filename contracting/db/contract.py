from contracting.compilation.compiler import ContractingCompiler
from contracting.db.driver import ContractDriver
from contracting.execution.runtime import rt
from types import ModuleType
from contracting.stdlib import env
from contracting import config

driver = rt.env.get('__Driver') or ContractDriver()


class Contract:
    def __init__(self, driver: ContractDriver=driver):
        self._driver = driver

    def submit(self, name, code, owner=None, constructor_args={}):

        c = ContractingCompiler(module_name=name)

        code_obj = c.parse_to_code(code, lint=True)

        # ctx = ModuleType('context')
        #
        # ctx.caller = rt.ctx[-1]
        # ctx.this = name
        # ctx.signer = rt.ctx[0]
        #
        scope = env.gather()
        scope.update({'__contract__': True})
        scope.update(rt.env)

        exec(code_obj, scope)

        if scope.get(config.INIT_FUNC_NAME) is not None and constructor_args is not None:
            scope[config.INIT_FUNC_NAME](**constructor_args)

        now = scope.get('now')
        if now is not None:
            self._driver.set_contract(name=name, code=code_obj, owner=owner, overwrite=False, timestamp=now)
        else:
            self._driver.set_contract(name=name, code=code_obj, owner=owner, overwrite=False)
