import pickle
#TODO datetime.datetime.now() shall be implemented / modified
from datetime import datetime
from datetime import timedelta

#TODO please change so that it can be imported from seneca_internal
supported_db_types = [int, str, bool, float, list, set]
import hashlib

#TODO replace with crypto
def sha256(secret):
    m = hashlib.sha256()
    m.update(secret.encode())
    return m.hexdigest()

class enum(dict):
    def __init__(self, *args, **kwargs):
        for idx, n in enumerate(args):
            setattr(self, n, idx)
            setattr(self, str(idx), n)

    def __getitem__(self, attr):
        return getattr(self, str(attr))

exports = {
    'pickle': pickle,
    'datetime': datetime,
    'timedelta': timedelta,
    'enum': enum,
    'sha256': sha256,
    'supported_db_types': supported_db_types
}


def run_tests():
    '''
    # TODO: Write tests for this module.
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
