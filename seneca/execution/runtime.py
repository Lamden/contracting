from collections import deque
from seneca import config


class Runtime:
    ctx = deque(maxlen=config.RECURSION_LIMIT)
