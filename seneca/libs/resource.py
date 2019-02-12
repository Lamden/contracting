import sys
from seneca.constants.config import RECURSION_LIMIT


def set_resource_limits():
    sys.setrecursionlimit(RECURSION_LIMIT)