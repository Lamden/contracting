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
        self.writes = defaultdict(set)
        self.reads = defaultdict(set)
        self.outputs = defaultdict(str)

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

    def reset_contract_data(self, contract_idx: int):
        """
        Resets the reads list and modification list for the contract at index idx.
        """
        self.writes[contract_idx].clear()
        self.reads[contract_idx].clear()
        self.outputs[contract_idx] = ''

    # TODO better interface
    # Abstraction for get_modified_keys/reset_keys is very weak. I don't think they will work with complex data types
    def get_modified_keys(self) -> set:
        return set()

    def reset_key(self, key):
        pass


class CRDataGetSet(CRDataBase, dict):
    NAME = 'getset'

    def _get_modified_keys(self):
        # TODO this needs to return READs that have had their original values changed too!
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
        return ''.join('SET {} {};'.format(k, self[k]['mod'].decode()) for k in sorted(modified_keys))

    def get_state_for_idx(self, contract_idx: int) -> str:
        return self.outputs[contract_idx]

    # TODO remove this API, i dont think we'll be needing it
    def should_rerun(self, contract_idx: int) -> bool:
        # A contract should rerun if any of the keys that it read/wrote have changed on either common or master
        all_rw = self.writes[contract_idx].union(self.reads[contract_idx])

        for mod in all_rw:
            latest_val = None
            # Get 'latest' value for key mod, pulling first from common layer, than master
            if self.working.exists(mod):
                latest_val = self.working.get(mod)
            elif self.master.exists(mod):
                latest_val = self.master.get(mod)

            if latest_val != self[mod]['og']:
                return True

        return False

    @classmethod
    def merge_to_master(cls, working_db: redis.StrictRedis, master_db: redis.StrictRedis, key: str):
        assert working_db.exists(key), "Key {} must exist in working_db to merge to master".format(key)
        val = working_db.get(key)
        master_db.set(key, val)

    def get_modified_keys(self) -> set:
        mods = set()
        for k in self:
            if (self.master.exists(k) and (self.master.get(k) != self[k]['og'])) or (
                    self.working.exists(k) and (self.working.get(k) != self[k]['og'])):
                mods.add(k)

        return mods

    def reset_key(self, key):
        # TODO I  think we are going to have problems when the key is different on both master AND common.
        # this is because if this context was built on top of another pending_db, and we are not the first subblock,
        # should we use the common layer (which presumably a prior sb copied from the updated master), or do we use
        # the updated master? I think we need some special logic for if this is subblock 0 then use master, otherwise
        # use common
        og_val = self[key]['og']

        # TODO do we need to reset the contracts that this key touched also???
        self[key]['mod'] = None

        # First, try and copy over master if it differs from original value
        if self.master.exists(key) and self.master.get(key) != og_val:
            self[key]['og'] = self.master.get(key)
        # Next, try to copy it over from common
        elif self.working.exists(key) and self.working.get(key) != og_val:
            self[key]['og'] = self.working.get(key)
        # Complain if neither of these conditions are met
        else:
            raise Exception("Attempted to reset key <{}> but key not found in common or master layer!".format(key))



    def get_contracts_for_keys(self, keys: set, reads=True, writes=True, exclude: set=None) -> List[int]:
        """ Get all contract indexes that had their reads and/or writes affected by the contracts in keys"""
        pass
        # contract_idxs = []
        #
        # for idx in range(max(len(self.reads), len(self.writes))):
        #     if reads and (idx in self.reads):
        #         if len(self.reads) > 0:
        #
        # if reads:
        #     for idx, mods in self.reads:
        #         if len(keys.intersection(mods)) > 0 and c



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

        # TODO deques are probobly more optimal than using arrays here
        # run_results is a list of strings, representing the return code of contracts (ie 'SUCC', 'FAIL', ..)
        self.run_results = []
        self.contracts = []  # A list of ContractionTransaction objects. SenecaClient should append as it runs contracts
        self.input_hash = None  # Input hash should be set by SenecaClient once a new sub block is started
        self.merged_to_common = False

    @property
    def next_contract_idx(self):
        assert len(self.contracts) == len(self.run_results), "Oh dear...a logic error is present"  # TODO remove
        return len(self.contracts)

    def add_contract_result(self, contract, result: str):
        assert len(self.contracts) == len(self.run_results), "Oh dear...a logic error is present"  # TODO remove
        self.contracts.append(contract)
        self.run_results.append(result)

    def update_contract_result(self, contract_idx: int, result: str):
        assert len(self.contracts) == len(self.run_results), "Oh dear...a logic error is present"  # TODO remove
        assert len(self.contracts) > contract_idx, "contract_idx {} out of bounds. Only {} contracts in self.contracts"\
                                                   .format(contract_idx, len(self.contracts))
        self.log.debugv("Updating run result for contract idx {} to <{}>".format(contract_idx, result))
        self.run_results[contract_idx] = result

    def reset(self, reset_db=True):
        """ Resets all state held by this container. """
        # TODO i think this would be a lot easier if we just scrapped this whole CRDataContainer object and made a new
        # one, but then would we have to worry about memory leaks? idk but either way screw python
        def _is_subclass(obj, subs: tuple):
            """ Utility method. Returns true if 'obj' is a subclass of any of the classes in subs """
            for s in subs:
                if issubclass(type(obj), s): return True
            return False

        self.log.debug("Reseting CRData with reset_db={}".format(reset_db))
        if reset_db:
            self.working_db.flushdb()

        # Reset this object's state
        self.merged_to_common = False
        self.input_hash = None
        self.run_results.clear()
        self.contracts.clear()
        # TODO is this ok resetting all the CRData's like this? Should we worry about memory leaks? --davis
        self.cr_data = {name: obj(master_db=self.master_db, working_db=self.working_db) for name, obj in
                        CRDataBase.registry.items()}

    def get_state_for_idx(self, contract_idx: int) -> str:
        """
        Returns the state for the contract at the specified index
        """
        assert contract_idx < len(self.contracts), "Contract index {} out of bounds for self.contracts of length {}" \
                                                   .format(contract_idx, len(self.contracts))

        state_str = ''
        for key in sorted(self.cr_data.keys()):  # We sort the keys so that output will always be deterministic
            state_str += self.cr_data[key].get_state_for_idx(contract_idx)
        return state_str

    def get_subblock_rep(self) -> List[tuple]:
        """
        Returns a list of tuples. There will be one tuple for each contract in self.contracts, and tuples will be of the
        form (contract, status, state). contract will be an instance of ContractTransaction. Status will be a string
        representing the execution status of the contract (fail/succ/ect). State will be a string that represents the
        changes to state made by that contract.
        """
        assert len(self.contracts) == len(self.run_results), "you done shit the bed again davis"
        assert self.merged_to_common, "You should have merged to common before trying to get the subblock rep"

        return [(self.contracts[i], self.run_results[i], self.get_state_for_idx(i)) for i in range(len(self.contracts))]

    def should_rerun(self, contract_idx: int) -> bool:
        """
        Returns true if the contract at index 'contract_idx' needs to be rerun. A contract needs to be rerun if any of
        its read/write operations represent values that have been changedb.
        NOTE: This assumes smart contracts ALWAYS assert on values they have written to. Under this logic, asserts on
        read values will not be honored.
        """
        return True in (obj.should_rerun(contract_idx) for obj in self.cr_data.values())

    def iter_rerun_indexes(self):
        pass
        # build a set of all reads/write that have their original value changed
        # copy, from common layer, to the new original value, and set the modified value to None
        # build a min heap of contract indexes that need to be run by check contract's mod list
        # reset the contract data before you rerun it
        # loop

        # PREFER MASTER VALUE when copying keys over. if og should have been copied from master during exec phase,
        # so if master is diff from og that means another block changed master, and that value should be prefered

        # what if both master and common differ from the orig values? which ones do you use?
        # we would need to track original master value (at time of the read). or just ignore this problem until
        # we implement proper chaining of db reads

    def reset_contract_data(self, contract_idx: int):
        """
        Resets the reads list and modification list for the contract at index idx.
        """
        for obj in self.cr_data.values():
            obj.reset_contract_data(contract_idx)

    def merge_to_common(self):
        assert not self.merged_to_common, "Already merged to common! merge_to_common should only be called once"

        for obj in self.cr_data.values():
            obj.merge_to_common()

        self.merged_to_common = True

    @classmethod
    def merge_to_master(cls, working_db: redis.StrictRedis, master_db: redis.StrictRedis):
        from seneca.engine.client import Macros  # to avoid cyclic imports

        for key in working_db.keys():
            # Ignore Phase keys
            if key in Macros.ALL_MACROS:
                continue

            t = working_db.type(key)

            if t == b'string':
                CRDataGetSet.merge_to_master(working_db, master_db, key)
            elif t == b'hash':
                CRDataHMap.merge_to_master(working_db, master_db, key)
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


"""
THOUGHT

each CRData has state variables for this rerun process, including
- internal list of contracts that HAVE been rerun?
- 

SHOULD WE ALSO MAINTAIN a mapping of keys to contracts that read/write them? Otherwise we have to do this o(n) 
everytime.. 

JUST RAISE AN ASSERTION FOR NOW IF A NEW KEY IS MODIFIED 

1) at start of rerun, CRData gets all contracts that have had their original values changed (on common or master)
2) copy over new values into effected key's original values (prioritize master if master is diff). Set mod value to None
3) if 
"""
