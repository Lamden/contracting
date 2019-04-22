import import_this

@seneca_export
def test():
    a = import_this.howdy()
    a -= 1000
    return a