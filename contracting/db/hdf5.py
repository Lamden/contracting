import h5py
from contracting.db.encoder import encode, decode

_groups_with_values = []

def _store_group_if_has_value_cb(name, obj):
    global _groups_with_values
    if 'value' in obj.attrs:
        _groups_with_values.append(name)

def set_value(filename, group_name, value):
    with h5py.File(filename, 'a') as f:
        if group_name not in f:
            f.create_group(group_name)
        ev = encode(value)
        f[group_name].attrs.create('value', ev, dtype='S'+str(len(ev)))

def get_value(filename, group_name):
    try:
        with h5py.File(filename, 'r') as f:
            return decode(f[group_name].attrs['value'])
    except:
        return None

def del_value(filename, group_name):
    with h5py.File(filename, 'a') as f:
        if group_name in f and 'value' in f[group_name].attrs:
            del f[group_name].attrs['value']

def get_groups(filename):
    global _groups_with_values
    _groups_with_values = []
    with h5py.File(filename, 'r') as f:
        f.visititems(_store_group_if_has_value_cb)

    return _groups_with_values
