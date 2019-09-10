@export
def get_owner(s):
    m = importlib.import_module(s)
    return importlib.owner_of(m)

@export
def owner_of_this():
    return ctx.owner
