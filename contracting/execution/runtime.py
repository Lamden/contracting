from collections import deque
import sys
from .. import config
import contracting
import os
from .metering.tracer import Tracer


class Runtime:
    cu_path = contracting.__path__[0]
    cu_path = os.path.join(cu_path, 'execution', 'metering', 'cu_costs.const')

    os.environ['CU_COST_FNAME'] = cu_path

    ctx = deque(maxlen=config.RECURSION_LIMIT)
    ctx.append('__main__')

    loaded_modules = []

    env = {}
    stamps = 0

    tracer = Tracer()

    signer = None
    ctx2 = deque(maxlen=config.RECURSION_LIMIT)

    @classmethod
    def set_up(cls, stmps, meter):
        if meter:
            cls.stamps = stmps
            cls.tracer.set_stamp(stmps)
            cls.tracer.start()

    @classmethod
    def clean_up(cls):
        cls.tracer.stop()
        cls.tracer.reset()
        cls.stamps = 0

        cls.ctx = deque(maxlen=config.RECURSION_LIMIT)
        cls.ctx2 = deque(maxlen=config.RECURSION_LIMIT)

        cls.ctx.append('__main__')

        cls.signer = None


        for mod in cls.loaded_modules:
            if sys.modules.get(mod) is not None:
                del sys.modules[mod]

        cls.loaded_modules = []
        cls.env = {}


rt = Runtime()
