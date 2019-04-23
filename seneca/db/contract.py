from ..execution.compiler import SenecaCompiler
from ..db.driver import ContractDriver
from ..execution.runtime import rt
from types import ModuleType
from ..stdlib import env


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