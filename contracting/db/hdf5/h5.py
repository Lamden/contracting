import h5py
from contracting.db.encoder import encode, decode
import contracting.db.hdf5.h5c as h5c

GROUP_SEPARATOR = '/'
_groups = []

def _store_group_if_has_value_cb(name, obj):
    global _groups
    if 'value' in obj.attrs:
        _groups.append(name)

def set_value(filepath, group, value):
    h5c.set(filepath, group, encode(value))

def get_value(filepath, group):
    return decode(h5c.get(filepath, group))

def del_value(filepath, group):
    h5c.delete(filepath, group)

def get_groups(filepath):
    global _groups
    _groups = []
    with h5py.File(filepath, 'r') as f:
        f.visititems(_store_group_if_has_value_cb)

    return _groups
