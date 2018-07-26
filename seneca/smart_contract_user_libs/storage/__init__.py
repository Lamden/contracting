import importlib
import os
import seneca.seneca_internal.util as util

from seneca.seneca_internal.util import manual_import
path = os.path.dirname(__file__)

exports = {}

# TODO: Confirm if this init work without this stuff?
for f in os.listdir(path):
    full_f_path = os.path.join(path, f)
    if full_f_path == __file__:
        pass
    elif f == '__pycache__':
        pass
    else:
        mod_name = f.split('.')[0]
        m = manual_import(full_f_path, mod_name)
        if m['exports'] is not None and type(m['exports']) == dict:
            exports[mod_name] = util.dict_to_nt(m['exports'], 'module')
        else:
            exports[mod_name] = m['exports']


def run_tests(_):
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
