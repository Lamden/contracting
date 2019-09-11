from ...execution.runtime import rt
from contextlib import ContextDecorator
from types import ModuleType
from ...db.driver import ContractDriver


class __export(ContextDecorator):
    def __init__(self, contract):
        self.contract = contract

    def __enter__(self):
        ctx = ModuleType('context')

        driver = rt.env.get('__Driver') or ContractDriver()

        ctx.owner = driver.get_owner(self.contract)
        ctx.caller = rt.ctx[-1]
        ctx.this = self.contract
        ctx.signer = rt.ctx[0]

        globals()['ctx2'] = ctx

        rt.ctx2.append(self.contract)

    def __exit__(self):
        rt.ctx2.pop()


@__export('erc20')
def activity():
    print('Some time consuming activity goes here')

activity()