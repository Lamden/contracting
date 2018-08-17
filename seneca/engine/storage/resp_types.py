class RType(): pass
class RScalar(RType): pass
# TODO: decide if Raw and String are actually needed,
class ScalarRaw(RScalar): pass
class ScalarString(RScalar): pass
class ScalarInt(RScalar): pass
class ScalarFloat(RScalar): pass

class RHash(RType): pass
class RList(RType): pass
class RSet(RType): pass
class RSortedSet(RType): pass

# TODO: Make a class for hset, may look a bit like row polymorphism
