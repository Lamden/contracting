from collections import deque
from seneca import config


class Runtime:
    ctx = deque(maxlen=config.RECURSION_LIMIT)
    ctx.append('__main__')

rt = Runtime()
