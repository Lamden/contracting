from ...execution.runtime import rt
from contextlib import ContextDecorator
from types import ModuleType
from ...db.driver import ContractDriver
from collections import deque

ctx = ModuleType('context')


class __export(ContextDecorator):
    def __init__(self, contract):
        self.contract = contract

    def __enter__(self):
        print('entering')
        driver = rt.env.get('__Driver') or ContractDriver()

        ctx.owner = driver.get_owner(self.contract)

        context.d.push(self.contract)

        rt.ctx2.push(self.contract)
        print(rt.ctx2.d)

        if rt.ctx2.last_parent() == self.contract:
            ctx.caller = rt.signer
        else:
            ctx.caller = rt.ctx2.last_parent()

        if ctx.owner is not None and ctx.owner != ctx.caller:
            raise Exception('Caller is not the owner!')

        ctx.this = self.contract
        ctx.signer = rt.signer

        print(vars(ctx))

    def __exit__(self, *args, **kwargs):
        print('exiting')

        if len(rt.ctx2.d) > 1:
            rt.ctx2.pop()

        print(rt.ctx2.d)

        if rt.ctx2.last_parent() == self.contract:
            ctx.caller = rt.signer
        else:
            ctx.caller = rt.ctx2.last_parent()
        ctx.this = self.contract
        ctx.signer = rt.signer


exports = {
    '__export': __export,
    'ctx': ctx,
    'rt': rt,
}