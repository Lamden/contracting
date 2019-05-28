from contracting.compilation.compiler import ContractingCompiler
from ..db.driver import ContractDriver
from ..execution.runtime import rt
from types import ModuleType
from ..stdlib import env
from .. import config

driver = rt.env.get('__Driver') or ContractDriver()

class Contract:
    def __init__(self, driver: ContractDriver=driver):
        self._driver = driver

    def submit(self, name, code, author):
        #
        # spec = importlib.util.find_spec(name)
        # if not isinstance(spec.loader, DatabaseLoader):
        #     raise ImportError("module {} cannot be named a Python builtin name.".format(name))
        #
        # assert self._driver.get_contract(name) is None, 'Module {} already exists'.format(name)

        c = ContractingCompiler(module_name=name)

        code_obj = c.parse_to_code(code, lint=True)

        ctx = ModuleType('context')

        ctx.caller = rt.ctx[-1]
        ctx.this = name
        ctx.signer = rt.ctx[0]

        scope = env.gather()
        scope.update({'ctx': ctx})
        scope.update({'__contract__': True})
        scope.update(rt.env)

        exec(code_obj, scope)

        if scope.get(config.INIT_FUNC_NAME) is not None:
            scope[config.INIT_FUNC_NAME]()

        self._driver.set_contract(name=name, code=code_obj, author=author, overwrite=False)
