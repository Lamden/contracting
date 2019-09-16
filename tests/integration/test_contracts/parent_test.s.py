@export
def get_val_from_child(s):
    m = importlib.import_module(s)
    return m.get_value()
