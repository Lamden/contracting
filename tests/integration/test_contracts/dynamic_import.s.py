@export
def import_thing(name: str):
    return importlib.import_module(name)