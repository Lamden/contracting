import h5py
from contracting.db.encoder import encode, decode

GROUP_SEPARATOR = '/'
_groups = []

def _store_group_if_has_value_cb(name, obj):
    global _groups
    if 'value' in obj.attrs:
        _groups.append(name)

def set_value(filename, group, value):
    with h5py.File(filename, 'a') as f:
        if group not in f:
            f.create_group(group)
        ev = encode(value)
        f[group].attrs.create('value', ev, dtype='S'+str(len(ev)))

def get_value(filename, group):
    try:
        with h5py.File(filename, 'r') as f:
            return decode(f[group].attrs['value'])
    except:
        return None

def del_value(filename, group):
    with h5py.File(filename, 'a') as f:
        if group in f and 'value' in f[group].attrs:
            del f[group].attrs['value']

def get_groups(filename):
    global _groups
    _groups = []
    with h5py.File(filename, 'r') as f:
        f.visititems(_store_group_if_has_value_cb)

    return _groups
