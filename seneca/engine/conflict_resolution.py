import redis
import functools
# TODO -- clean this file up


class RedisProxy:

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, contract_idx: int,
                 finalize=False):
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.finalize = finalize
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

    def __getattr__(self, item):
        from seneca.engine.cr_commands import CRCmdBase  # To avoid cyclic imports
        assert item in CRCmdBase.registry, "redis operation {} not implemented for conflict resolution".format(item)

        return CRCmdBase.registry[item](working_db=self.working_db, master_db=self.master_db,
                                        sbb_idx=self.sbb_idx, contract_idx=self.contract_idx,
                                        finalize=self.finalize)


class RedisOperation:
    def __init__(self, op_name: str, key: str, *args, **kwargs):
        self.op_name, self.key, self.args, self.kwargs = op_name, key, args, kwargs


class CRDataMeta(type):
    def __new__(cls, clsname, bases, clsdict):
        clsobj = super().__new__(cls, clsname, bases, clsdict)
        if not hasattr(clsobj, 'registry'):
            clsobj.registry = {}

        # Only add strucutres that have the 'NAME' field set
        if 'NAME' in clsdict:
            clsobj.registry[clsdict['NAME']] = clsobj
        return clsobj


class CRDataBase(metaclass=CRDataMeta):
    def __init__(self, master_db: redis.StrictRedis, working_db: redis.StrictRedis):
        self.master, self.working = master_db, working_db

    def merge_to_common(self):
        """
        Merges the subblock specific data to the common layer, rerunning contracts as needed.
        """
        raise NotImplementedError()


class CRDataGetSet(CRDataBase):
    NAME = 'getset'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = {}

    def merge_to_common(self):
        pass


class CRDataDelete(CRDataBase):
    NAME = 'del'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deleted_keys = set()

    def merge_to_common(self):
        pass


class CRDataOperations(CRDataBase):
    NAME = 'ops'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ops = []  # A list of RedisOperation instances
        self.mods = []  # A list of list of modifications

    def merge_to_common(self):
        pass


class CRDataContainer:

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, finalize=False):
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.finalize = finalize
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx = sbb_idx

        # cr_data holds instances of CRDataBase. The key is the 'NAME' field specified in the CRDataBase subclass
        self.cr_data = {name: obj(master_db=self.master_db, working_db=self.working_db) for name, obj in
                        CRDataBase.registry.items()}

        # TODO WHY DO WE NEED WORKING DB? CUZ THATS WHERE WE STORE THE COMMON LAYER. SBB SPECIFIC IN PYTHON MEMORY

    def merge_to_master(self):  # TODO should i just call this merge?
        pass


print("CRDataMetaRegistery")
for k, v in CRDataBase.registry.items():
    print("{}: {}".format(k, v))