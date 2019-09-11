from ...execution.runtime import rt
from contextlib import ContextDecorator
from types import ModuleType
from ...db.driver import ContractDriver

ctx = ModuleType('context')


class __export(ContextDecorator):
    def __init__(self, contract):
        self.contract = contract

    def __enter__(self):
        driver = rt.env.get('__Driver') or ContractDriver()

        ctx.owner = driver.get_owner(self.contract)
        ctx.caller = rt.ctx[-1]
        ctx.this = self.contract
        ctx.signer = rt.ctx[0]

        rt.ctx2.append(self.contract)

    def __exit__(self, *args, **kwargs):
        rt.ctx2.pop()


exports = {
    '__export': __export,
    'ctx2': ctx
}