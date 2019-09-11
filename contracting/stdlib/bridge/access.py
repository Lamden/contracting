from ...execution.runtime import rt
from contextlib import ContextDecorator
from types import ModuleType
from ...db.driver import ContractDriver

ctx = ModuleType('context')


class __export(ContextDecorator):
    def __init__(self, contract):
        self.contract = contract

    def __enter__(self):
        print('entering {}'.format(self.contract))
        if rt.ctx2[-1] != self.contract:
            print('contract: {}'.format(self.contract))
            rt.ctx2.append(self.contract)

        driver = rt.env.get('__Driver') or ContractDriver()

        ctx.owner = driver.get_owner(self.contract)

        if len(rt.ctx2) < 2:
            ctx.caller = rt.signer
        else:
            if rt.ctx2[-1] == self.contract:
                ctx.caller = rt.ctx2[-2]
            else:
                ctx.caller = rt.ctx2[-1]

        ctx.this = self.contract
        ctx.signer = rt.signer

    def __exit__(self, *args, **kwargs):
        print('popping from {}'.format(self.contract))
        rt.ctx2.pop()


exports = {
    '__export': __export,
    'ctx2': ctx,
    'rt': rt,
}