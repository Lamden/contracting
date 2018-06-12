import importlib
import os
import seneca.seneca_internal.util as util

from seneca.seneca_internal.util import manual_import
path = os.path.dirname(__file__)



exports = {}

for f in os.listdir(path):
    full_f_path = os.path.join(path, f)
    if full_f_path == __file__:
        pass
    elif f == '__pycache__':
        pass
    else:
        mod_name = f.split('.')[0]
        m = manual_import(full_f_path, mod_name)
        if m['exports'] is not None:
            exports[mod_name] = util.dict_to_nt(m['exports'], 'module')

def run_tests():
    print(path)
