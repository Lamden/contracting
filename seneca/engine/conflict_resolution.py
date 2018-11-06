import redis
from collections import defaultdict
from seneca.libs.logger import get_logger
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

        # Only add classes that have the 'NAME' field set
        if 'NAME' in clsdict:
            clsobj.registry[clsdict['NAME']] = clsobj
        return clsobj


class CRDataBase(metaclass=CRDataMeta):
    def __init__(self, master_db: redis.StrictRedis, working_db: redis.StrictRedis):
        super().__init__()
        self.log = get_logger(type(self).__name__)
        self.master, self.working = master_db, working_db
        self.mods = []

    def merge_to_common(self):
        """
        Merges the subblock specific data to the common layer
        """
        raise NotImplementedError()

    def get_state_rep(self) -> str:
        """
        Updates the 'state' list for the changes represented in this data structure. The state list is a list of outputs
        or modifications from every contract.
        """
        raise NotImplementedError()

    def get_state_for_idx(self, contract_idx: int) -> str:
        """
        Gets a state representation string for a particular contract index. This should be overwritten by all subclasses
        that track any sort of state modifications
        """
        return ''

    def should_rerun(self, contract_idx: int) -> bool:
        """
        Returns true if the contract at index 'contract_idx' needs to be rerun. A contract needs to be rerun if any of
        its write operations represent values that have been changed.
        NOTE: This assumes smart contracts assert on values they have written to
        """
        raise NotImplementedError()


class CRDataGetSet(CRDataBase, dict):
    NAME = 'getset'

    def _get_modified_keys(self):
        return set().union((key for key in self if self[key]['og'] != self[key]['mod'] and self[key]['mod'] is not None))

    def merge_to_common(self):
        modified_keys = self._get_modified_keys()
        for key in modified_keys:
            self.working.set(key, self[key]['mod'])

    def get_state_rep(self) -> str:
        """
        Return a representation of all redis DB commands to update to the absolute state in minimum operations
        :return: A string with all redis command in raw executable form, delimited by semicolons
        """
        modified_keys = self._get_modified_keys()
        # Need to sort the modified_keys so state output is deterministic
        return ''.join('SET {} {};'.format(k, self[k]['mod']) for k in sorted(modified_keys))

    def get_state_for_idx(self, contract_idx: int) -> str:
        if contract_idx >= len(self.mods):  # Edge condition, must check array bounds
            return ''

        mods = self.mods[contract_idx]
        return ''.join('SET {} {};'.format(k, self[k]['mod']) for k in sorted(mods))

    def should_rerun(self, contract_idx: int) -> bool:
        if contract_idx >= len(self.mods):  # Check array out of bounds
            return False

        # Return True if the common layer key exists and is different than the original
        mod_set = self.mods[contract_idx]
        for mod in self.mods[contract_idx]:
            # Get 'latest' value for key mod, pulling first from common layer, than master
            if self.working.exists(mod):
                latest_val = self.working.get(mod)
            else:
                latest_val = self.master.get(mod)

            if latest_val != self[mod]['og']:
                return True

        return False

    @classmethod
    def merge_to_master(cls, working_db: redis.StrictRedis, master_db: redis.StrictRedis, key: str):
        assert working_db.exists(key), "Key {} must exist in working_db to merge to master".format(key)
        val = working_db.get(key)
        master_db.set(key, val)


class CRDataHMap(CRDataBase, defaultdict):
    NAME = 'hm'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_factory = dict

    def _get_modified_keys(self) -> dict:
        """
        Returns a dict of sets. Key is key in the hmap, and set is a list of modified fields for that key
        """
        mods_dict = defaultdict(set)
        for key in self:
            for field in self[key]:
                if self[key][field]['og'] != self[key][field]['mod']:
                    mods_dict[key].add(field)

        return mods_dict

    def merge_to_common(self):
        return False  # TODO implement
        raise NotImplementedError()

    def get_state_rep(self):
        return False  # TODO implement
        raise NotImplementedError()

    def should_rerun(self, contract_idx: int) -> bool:
        return False  # TODO implement
        raise NotImplementedError()

    @classmethod
    def merge_to_master(cls, working_db: redis.StrictRedis, master_db: redis.StrictRedis, key: str):
        assert working_db.exists(key), "Key {} must exist in working_db to merge to master".format(key)

        all_fields = working_db.hkeys(key)
        for field in all_fields:
            val = working_db.hget(key, field)
            master_db.hset(key, field, val)


class CRDataDelete(CRDataBase, set):
    NAME = 'del'

    def merge_to_common(self):
        return False  # TODO implement
        raise NotImplementedError()

    def get_state_rep(self):
        return False  # TODO implement
        raise NotImplementedError()

    def should_rerun(self, contract_idx: int) -> bool:
        return False  # TODO implement
        raise NotImplementedError()


class CRDataOperations(CRDataBase, list):
    """
    CRDataOperations is a list of RedisOperation instances.
    """
    NAME = 'ops'

    def merge_to_common(self):
        pass  # TODO implement
        # raise NotImplementedError()

    def get_state_rep(self):
        pass  # TODO implement
        # raise NotImplementedError()

    def should_rerun(self, contract_idx: int) -> bool:
        pass  # TODO implement
        # raise NotImplementedError()


class CRDataOutputs(CRDataBase, list):
    """
    This structure is a list of tuples. The index of the outer list correspons to the output of the contract with that
    same index. The tuple itself always has 2 elements, and is of the form [RESULT, OUTPUT], where
    """
    NAME = 'out'

    def merge_to_common(self):
        return False  # TODO implement
        raise NotImplementedError()

    def get_state_rep(self):
        return False  # TODO implement
        raise NotImplementedError()

    def should_rerun(self, contract_idx: int) -> bool:
        return False


class CRDataContainer:

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, finalize=False):
        self.log = get_logger(type(self).__name__)
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.finalize = finalize
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx = sbb_idx

        # cr_data holds instances of CRDataBase. The key is the 'NAME' field specified in the CRDataBase subclass
        # For convenience, all these keys are directly accessible from this CRDataContainer instance (see __getitem__)
        self.cr_data = {name: obj(master_db=self.master_db, working_db=self.working_db) for name, obj in
                        CRDataBase.registry.items()}

        # run_results is a list of strings, representing the return code of contracts (ie 'SUCC', 'FAIL', ..)
        self.run_results = []

        self.merged_to_common = False
        self.input_hash = None  # Input hash should be set by SenecaClient once a new sub block is started

    def update_contract_result(self, contract_idx: int, result: str):
        self.log.debugv("Updating run result for contract idx {} to <{}>".format(contract_idx, result))

        # Add empty elements until run_results is the appropriate size
        if contract_idx >= len(self.run_results):
            for _ in range(contract_idx + 1 - len(self.run_results)):
                self.run_results.append('')

        self.run_results[contract_idx] = result

    def reset(self, reset_db=True):
        """
        Resets all state held by this container.
        """
        self.log.debug("Reseting CRData with reset_db={}".format(reset_db))
        if reset_db:
            self.working_db.flushdb()
            
        for container in self.cr_data.values():
            container.mods.clear()
            if type(container) in (list, set, dict, defaultdict):
                container.clear()
            else:
                raise NotImplementedError("No reset logic implemented for container of type {}".format(type(container)))

    def get_state_for_idx(self, contract_idx: int) -> str:
        # I assume the values will be iterated over deterministically on all different processes. Is this sane? --davis
        state_str = ''
        for obj in self.cr_data.values():
            state_str += obj.get_state_for_idx(contract_idx)
        return state_str

    def should_rerun(self, contract_idx: int):
        """
        Returns true if the contract at index 'contract_idx' needs to be rerun. A contract needs to be rerun if any of
        its write operations represent values that have been changed.
        NOTE: This assumes smart contracts ALWAYS assert on values they have written to. Under this logic, asserts on
        read values will not be honored.
        """
        return True in (obj.should_rerun(contract_idx) for obj in self.cr_data.values())

    def merge_to_common(self):
        assert not self.merged_to_common, "Already merged to common! merge_to_common should only be called once"

        for obj in self.cr_data.values():
            obj.merge_to_common()

        self.merged_to_common = True

    # TODO merge_to_master can probly be a class method, we just have to pass in working_db
    def merge_to_master(self):
        from seneca.engine.client import Macros  # to avoid cyclic imports

        for key in self.working_db.keys():
            # Ignore Phase keys
            if key in Macros.ALL_MACROS:
                continue

            t = self.working_db.type(key)

            if t == b'string':
                CRDataGetSet.merge_to_master(self.working_db, self.master_db, key)
            elif t == b'hash':
                CRDataHMap.merge_to_master(self.working_db, self.master_db, key)
            else:
                raise NotImplementedError("No logic implemented for copying key <{}> of type <{}>".format(key, t))

    def __getitem__(self, item):
        assert item in self.cr_data, "No structure named {} in cr_data. Only keys available: {}"\
                                     .format(item, list(self.cr_data.keys()))
        return self.cr_data[item]


class RedisProxy:

    def __init__(self, sbb_idx: int, contract_idx: int, data: CRDataContainer, finalize=False):
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.finalize = finalize
        self.data = data
        self.working_db, self.master_db = data.working_db, data.master_db
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
