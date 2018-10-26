

class RObjectMeta(type):
    all_reads = set()
    all_writes = set()

    def __new__(cls, clsname, bases, clsdict):
        clsobj = super().__new__(cls, clsname, bases, clsdict)
        cls._combine_sets_if_exists(clsobj, '_READ_METHODS', 'all_reads')
        cls._combine_sets_if_exists(clsobj, '_WRITE_METHODS', 'all_writes')
        return clsobj

    @classmethod
    def _combine_sets_if_exists(cls, clsobj, set_to_add: str, set_to_add_to: str):
        """
        Adds all of the elements in set_to_add to set_to_add_to.
        """
        if hasattr(clsobj, set_to_add):
            assert hasattr(clsobj, set_to_add_to), "Class {} has no attribute {}".format(clsobj, set_to_add_to)
            set_to_add_to = getattr(clsobj, set_to_add_to)

            for element in getattr(clsobj, set_to_add):
                set_to_add_to.add(element)
