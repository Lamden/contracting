import redis
from collections import defaultdict
from typing import List
# TODO -- clean this file up


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
        super().__init__()
        self.master, self.working = master_db, working_db
        self.mods = []

    def get_rerun_set(self) -> set:
        """
        Returns a set of ints, represeting all contracts that need to be rerun as a result of their original reads being
        modified.
        :return: A set of integers
        """
        raise NotImplementedError()

    def merge_to_common(self):
        """
        Merges the subblock specific data to the common layer, rerunning contracts as needed.
        """
        raise NotImplementedError()

    def update_state_list(self):
        """
        Updates the 'state' list for the changes represented in this data structure. The state list is a list of outputs
        or modifications from every contract.
        """
        raise NotImplementedError()


class CRDataGetSet(CRDataBase, dict):
    NAME = 'getset'

    def merge_to_common(self):
        raise NotImplementedError()

    def update_state_list(self):
        raise NotImplementedError()

    def get_rerun_set(self) -> set:
        raise NotImplementedError()


class CRDataHMap(CRDataBase, defaultdict):
    NAME = 'hm'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_factory = dict

    def merge_to_common(self):
        raise NotImplementedError()

    def update_state_list(self):
        raise NotImplementedError()

    def get_rerun_set(self) -> set:
        raise NotImplementedError()


class CRDataDelete(CRDataBase, set):
    NAME = 'del'

    def merge_to_common(self):
        raise NotImplementedError()

    def update_state_list(self):
        raise NotImplementedError()

    def get_rerun_set(self) -> set:
        raise NotImplementedError()


class CRDataOperations(CRDataBase, list):
    """
    CRDataOperations is basically a list of RedisOperation instances.
    """
    NAME = 'ops'

    def merge_to_common(self):
        raise NotImplementedError()

    def update_state_list(self):
        raise NotImplementedError()

    def get_rerun_set(self) -> set:
        raise NotImplementedError()


class CRDataOutputs(CRDataBase, list):
    """
    This structure is a list of tuples. The index of the outer list correspons to the output of the contract with that
    same index. The tuple itself always has 2 elements, and is of the form [RESULT, OUTPUT], where
    """
    NAME = 'out'

    def merge_to_common(self):
        raise NotImplementedError()

    def update_state_list(self):
        raise NotImplementedError()

    def get_rerun_set(self) -> set:
        pass


# class CRDataModifications(CRDataBase, list):
#     """
#     Modifications are stored as a list of sets. The index of each the list corresponds to the index of the contract
#     that invokes modication, and the element itself is a set of modifications (a set of modified keys to be exact)
#     """
#     NAME = 'mods'
#
#     def merge_to_common(self):
#         raise NotImplementedError()
#
#     def update_state_list(self):
#         # There is no need to update state list for this data structure
#         pass
#
#     def get_rerun_set(self) -> set:
#         pass


class CRDataContainer:

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, finalize=False):
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.finalize = finalize
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx = sbb_idx

        # cr_data holds instances of CRDataBase. The key is the 'NAME' field specified in the CRDataBase subclass
        # For convenience, all these keys are directly accessible from this CRDataContainer instance (see __getitem__)
        self.cr_data = {name: obj(master_db=self.master_db, working_db=self.working_db) for name, obj in
                        CRDataBase.registry.items()}

    def reset(self):
        """
        Resets all state held by this container.
        """
        for container in self.cr_data.values():
            container.mods.clear()
            if type(container) in (list, set, dict, defaultdict):
                container.clear()
            else:
                raise NotImplementedError("No reset logic implemented for container of type {}".format(type(container)))

    def get_rerun_list(self) -> list:
        """
        Returns a list of ints, representing all contracts that need to be rerun as a result of their original reads
        being modified by another sub-block
        :return: A list of sorted integers
        """
        all_reruns = set()
        for obj in self.cr_data.values():
            all_reruns = all_reruns.union(obj.get_rerun_set())
        return sorted(all_reruns)

    def merge_to_master(self):  # TODO should i just call this merge?
        pass

    def merge_to_common(self):
        pass

    def __getitem__(self, item):
        assert item in self.cr_data, "No structure named {} in cr_data. Only keys available: {}"\
                                     .format(item, list(self.cr_data.keys()))
        return self.cr_data[item]


class RedisProxy:

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, contract_idx: int,
                 data: CRDataContainer, finalize=False):
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.finalize = finalize
        self.data = data
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

    def __getattr__(self, item):
        from seneca.engine.cr_commands import CRCmdBase  # To avoid cyclic imports -- TODO better solution?
        assert item in CRCmdBase.registry, "redis operation {} not implemented for conflict resolution".format(item)

        return CRCmdBase.registry[item](working_db=self.working_db, master_db=self.master_db,
                                        sbb_idx=self.sbb_idx, contract_idx=self.contract_idx, data=self.data,
                                        finalize=self.finalize)


# print("CRDataMetaRegistery")
# for k, v in CRDataBase.registry.items():
#     print("{}: {}".format(k, v))