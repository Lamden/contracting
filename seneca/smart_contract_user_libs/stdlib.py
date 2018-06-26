import pickle
from datetime import datetime

class enum(dict):
    def __init__(self, *args, **kwargs):
        for idx, n in enumerate(args):
            setattr(self, n, idx)
            setattr(self, str(idx), n)

    def __getitem__(self, attr):
        print(attr)
        return getattr(self, str(attr))

exports = {
    'pickle': pickle,
    'datetime': datetime,
    'enum': enum
}

def run_tests():
    pass
