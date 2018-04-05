# TODO: Implement auto_exports() and @export

def _make_exports(*args):
    #Todo: impelement for types allowable for export, throw exception on others.
    return {a.__name__: a for a in args}

exports = {'make_exports':_make_exports}
