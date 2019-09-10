@export
def get_owner(s):
    m = importlib.import_module(s)
    return importlib.owner_of(m)