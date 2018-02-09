def make_exports(*args):
    #Todo: impelement for types allowable for export, throw exception on others.
    return {a.__name__: a for a in args}
