from ...execution.runtime import rt
from contextlib import ContextDecorator
from types import ModuleType
from ...db.driver import ContractDriver
from collections import deque

ctx = ModuleType('context')


class Context:
    def __init__(self, base_state):
        self._state = []
        self._base_state = base_state

    def _context_changed(self, contract):
        if self._get_state()['this'] == contract:
            return False
        return True

    def _get_state(self):
        if len(self._state) == 0:
            return self._base_state
        return self._state[-1]

    def _add_state(self, state: dict):
        if self._context_changed(state['this']):
            self._state.append(state)

    def _pop_state(self):
        if len(self._state) > 0:
            self._state.pop(-1)

    @property
    def this(self):
        return self._get_state()['this']

    @property
    def caller(self):
        return self._get_state()['caller']

    @property
    def signer(self):
        return self._get_state()['signer']

    @property
    def owner(self):
        return self._get_state()['owner']


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
