from .bridge.orm import exports as orm_exports
from .bridge.hashing import exports as hash_exports
from .bridge.time import exports as time_exports


def gather():
    env = {}
    env.update(orm_exports)
    env.update(hash_exports)
    env.update(time_exports)
    return env
