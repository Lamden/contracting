from seneca.engine.util import auto_set_fields

class RSnapDependency:
    @auto_set_fields
    def __init__(self, address):
        pass


class TypeDependency(RSnapDependency): pass
class ValueDependency(RSnapDependency): pass


# TODO: A function that takes a Command and returns dependencies
# TODO: A function, given a serialized write and a read dep, determine if there's a conflict
