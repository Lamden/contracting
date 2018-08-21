class RType(): pass

class RNoValueExists(RType):
    def __repr__(self):
        return '<RESP (%s) %s>' % (self.__class__.__name__, str(self.__dict__))

# Scalar Types
class RScalar(RType):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<RESP (%s) %s>' % (self.__class__.__name__, str(self.__dict__))

class RScalarInt(RScalar): pass
class RScalarFloat(RScalar): pass

# Collections
class RHash(RType):
    # Address scheme ('key', 'key')
    pass
class RList(RType):
    # Address scheme ('key', 1)
    pass
class RSet(RType):
    # Just key
    pass

class RSortedSet(RType):


    pass

# TODO: Make a class for hset, may look a bit like row polymorphism

def make_rscalar(x):
    if isinstance(x, int):
        return RScalarInt(x)
    elif isinstance(x, float):
        return RScalarFloat(x)
    else:
        try:
            i = int(x)
            return RScalarInt(i)
        except ValueError:
            pass

        try:
            f = float(x)
            return RScalarFloat(f)
        except ValueError:
            pass

        assert isinstance(x, str)
        return RScalar(x)
