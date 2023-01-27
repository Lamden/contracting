import sys
from contracting import config
import contracting
import os
from contracting.execution.metering.tracer import Tracer


class Context:
    def __init__(self, base_state, maxlen=config.RECURSION_LIMIT):
        self._state = []
        self._base_state = base_state
        self._maxlen = maxlen

    def _context_changed(self, contract):
        if self._get_state()['this'] == contract:
            return False
        return True

    def _get_state(self):
        if len(self._state) == 0:
            return self._base_state
        return self._state[-1]

    def _add_state(self, state: dict):
        if self._context_changed(state['this']) and len(self._state) < self._maxlen:
            self._state.append(state)

    def _pop_state(self):
        if len(self._state) > 0:
            self._state.pop(-1)

    def _reset(self):
        self._state = []

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

    @property
    def entry(self):
        return self._get_state()['entry']

    @property
    def submission_name(self):
        return self._get_state()['submission_name']


_context = Context({
        'this': None,
        'caller': None,
        'owner': None,
        'signer': None,
        'entry': None,
        'submission_name': None
    })

WRITE_MAX = 1024 * 64

class Runtime:
    cu_path = contracting.__path__[0]
    cu_path = os.path.join(cu_path, 'execution', 'metering', 'cu_costs.const')

    os.environ['CU_COST_FNAME'] = cu_path

    loaded_modules = []

    env = {}
    stamps = 0

    writes = 0

    tracer = Tracer()

    signer = None

    context = _context

    @classmethod
    def set_up(cls, stmps, meter):
        if meter:
            cls.stamps = stmps
            cls.tracer.set_stamp(stmps)
            cls.tracer.start()

        cls.context._reset()

    @classmethod
    def clean_up(cls):
        cls.tracer.stop()
        cls.tracer.reset()
        cls.stamps = 0
        cls.writes = 0

        cls.signer = None

        for mod in cls.loaded_modules:
            if sys.modules.get(mod) is not None:
                del sys.modules[mod]

        cls.loaded_modules = []
        cls.env = {}

    @classmethod
    def deduct_read(cls, key, value):
        if cls.tracer.is_started():
            cost = len(key) + len(value)
            cost *= config.READ_COST_PER_BYTE
            cls.tracer.add_cost(cost)

    @classmethod
    def deduct_write(cls, key, value):
        if key is not None and cls.tracer.is_started():
            cost = len(key) + len(value)
            cls.writes += cost

            assert cls.writes < WRITE_MAX, 'You have exceeded the maximum write capacity per transaction!'

            stamp_cost = cost * config.WRITE_COST_PER_BYTE
            cls.tracer.add_cost(stamp_cost)


rt = Runtime()
