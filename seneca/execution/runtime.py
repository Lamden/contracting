from collections import deque
import sys
from .. import config
from ..db.driver import ContractDriver


class Context:
    def __init__(self):
        self.this = None
        self.signer = None
        self.caller = None

    def __enter__(self):
        self.caller = rt.ctx[-1]
        self.this = __name__
        self.signer = rt.ctx[0]
        rt.ctx.append(self.this)

    def __exit__(self, *args,  **kwargs):
        rt.ctx.pop()


class Runtime:
    ctx = deque(maxlen=config.RECURSION_LIMIT)
    ctx.append('__main__')
    driver = ContractDriver()
    loaded_modules = []
    env = {}

    @classmethod
    def clean_up(cls):
        cls.ctx = deque(maxlen=config.RECURSION_LIMIT)
        cls.ctx.append('__main__')

        for mod in cls.loaded_modules:
            if sys.modules.get(mod) is not None:
                del sys.modules[mod]

        cls.loaded_modules = []
        cls.env = {}


rt = Runtime()
