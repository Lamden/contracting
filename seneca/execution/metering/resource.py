import sys
from ...config import RECURSION_LIMIT


def set_resource_limits():
    # resource.setrlimit(resource.RLIMIT_STACK, (MEMORY_LIMIT, MEMORY_LIMIT))
    # resource.setrlimit(resource.RLIMIT_CPU, (CPU_TIME_LIMIT, CPU_TIME_LIMIT))
    sys.setrecursionlimit(RECURSION_LIMIT)
