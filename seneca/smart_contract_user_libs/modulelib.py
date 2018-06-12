# TODO: Implement auto_exports() and @export
_exports_dict = {}

def _make_exports(*args):
    #Todo: impelement for types allowable for export, throw exception on others.
    return {a.__name__: a for a in args}



def export(f):
    '''function decorator that adds function to export list.
    '''
    _exports_dict[f.__name__] = f
    return f


def make_exports():
    return _exports_dict




exports = {
    'make_exports': make_exports,
    'export': export
}
