from collections import deque
import sys
from .. import config
from ..db.driver import ContractDriver


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
