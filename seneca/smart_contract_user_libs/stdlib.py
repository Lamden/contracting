import pickle, hashlib
#TODO datetime.datetime.now() shall be implemented / modified
from datetime import datetime
from datetime import timedelta

#TODO please change so that it can be imported from seneca_internal
supported_db_types = [int, str, bool, float, list, set]

class enum(dict):
    def __init__(self, *args, **kwargs):
        for idx, n in enumerate(args):
            setattr(self, n, idx)
            setattr(self, str(idx), n)

    def __getitem__(self, attr):
        return getattr(self, str(attr))

def ripemd160(secret):
    h = hashlib.new('ripemd160')
    h.update(secret.encode())
    return h.hexdigest()

exports = {
    'pickle': pickle,
    'datetime': datetime,
    'timedelta': timedelta,
    'enum': enum,
    'supported_db_types': supported_db_types,
    'ripemd160': ripemd160
}

def run_tests():
    pass
