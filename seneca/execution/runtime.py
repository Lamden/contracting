from collections import deque
from seneca import config
from seneca.db.driver import ContractDriver


class Runtime:
    ctx = deque(maxlen=config.RECURSION_LIMIT)
    ctx.append('__main__')
    driver = ContractDriver()


rt = Runtime()
