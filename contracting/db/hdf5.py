import h5py
from contracting.db.encoder import encode, decode

_vars_with_values = []

def _store_var_if_has_value_cb(name, obj):
    global _vars_with_values
    if 'value' in obj.attrs:
        _vars_with_values.append(name)

def set_value(filename, variable, value):
    with h5py.File(filename, 'a') as f:
        if variable not in f:
            f.create_group(variable)
        ev = encode(value)
        f[variable].attrs.create('value', ev, dtype='S'+str(len(ev)))

def get_value(filename, variable):
    try:
        with h5py.File(filename, 'r') as f:
            return decode(f[variable].attrs['value'])
    except:
        return None

def del_value(filename, variable):
    with h5py.File(filename, 'a') as f:
        if variable in f and 'value' in f[variable].attrs:
            del f[variable].attrs['value']

def get_vars(filename):
    global _vars_with_values
    _vars_with_values = []
    with h5py.File(filename, 'r') as f:
        f.visititems(_store_var_if_has_value_cb)

    return _vars_with_values
