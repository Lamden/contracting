from collections import defaultdict
from ...logger import get_logger
from typing import List


# TODO this assumes stamps_to_tau will never change. We need more intricate logic to handle the case where it does...
STAMPS_KEY = 'currency:balances:black_hole'
CR_EXCLUDED_KEYS = ['currency:xrate:TAU_STP', STAMPS_KEY]


class CRDataGetSet(dict):
    def __init__(self, master_db, working_db):
        super().__init__()
        self.log = get_logger(type(self).__name__)
        self.master, self.working = master_db, working_db
        self.writes = defaultdict(set)
        self.outputs = defaultdict(str)
        self.redo_log = defaultdict(dict)

    def _get_modified_keys(self):
        return set().union((key for key in self if self[key]['og'] != self[key]['mod'] and self[key]['mod'] is not None))

    def get_state_for_idx(self, contract_idx: int) -> str:
        """
        Gets a state representation string for a particular contract index. """
        return self.outputs[contract_idx]

    def reset_contract_data(self, contract_idx: int):
        """ Resets the reads list and modification list for the contract at index idx. """
        self.writes[contract_idx].clear()
        self.outputs[contract_idx] = ''

    def merge_to_common(self):
        modified_keys = self._get_modified_keys()
        for key in modified_keys:
            self.working.set(key, self[key]['mod'])

    @classmethod
    def merge_to_master(cls, working_db, master_db, key: str):
        assert working_db.exists(key), "Key {} must exist in working_db to merge to master".format(key)
        val = working_db.get(key)
        master_db.set(key, val)

    def get_state_rep(self) -> str:
        """
        Return a representation of all ledis DB commands to update to the absolute state in minimum operations
        :return: A string with all ledis command in raw executable form, delimited by semicolons
        """
        modified_keys = self._get_modified_keys()
        # Need to sort the modified_keys so state output is deterministic
        return ''.join('SET {} {};'.format(k, self[k]['mod'].decode()) for k in sorted(modified_keys))

    def rollback_contract(self, contract_idx: int):
        self.log.debug("Reseting contract idx {}".format(contract_idx))
        if contract_idx not in self.redo_log:
            # TODO for dev, we raise an exception, as we do not expect contracts to read only w/o writing
            # raise Exception("Contract idx {} not in redo_log!".format(contract_idx))
            self.log.warning("Contract idx {} not in redo_log! Returning without any reverts".format(contract_idx))
            return

        self.reset_contract_data(contract_idx)

        for key in self.redo_log[contract_idx]:
            og_val = self.redo_log[contract_idx][key]
            # Remove the key entirely if value is none
            if og_val is None:
                self.log.debugv("Removing key {}".format(key))
                del self[key]
            # Otherwise, reset_db the key to the value before the contract
            else:
                self.log.debugv("Resetting key {} to value {}".format(key, og_val))
                self[key]['mod'] = og_val

            # Remove this contract idx from the key's affected contracts
            if key in self and contract_idx in self[key]['contracts']:
                self[key]['contracts'].remove(contract_idx)

    def revert_contract(self, contract_idx: int):
        assert contract_idx in self.redo_log, "Contract index {} not found in redo log!".format(contract_idx)

    def get_rerun_list(self, reset_keys=True) -> List[int]:
        mod_keys = self.get_modified_keys_recursive()
        assert STAMPS_KEY not in mod_keys, "Noooooooo mod keys {} has stamp key".format(mod_keys)
        contract_set = set()
        self.log.debugv("Modified keys for rerunning: {}".format(mod_keys))

        for key in mod_keys:
            contract_set = contract_set.union(self[key]['contracts'])
            if reset_keys:
                self.reset_key(key)

        self.log.debugv("CONTRACT SET TO RERUN: {}".format(contract_set))

        return sorted(contract_set)

    def get_modified_keys(self) -> set:
        mods = set()
        for k in self:
            if (self.master.exists(k) and (self.master.get(k) != self[k]['og'])) or (
                    self.working.exists(k) and (self.working.get(k) != self[k]['og'])):
                mods.add(k)

        return mods - {STAMPS_KEY, *CR_EXCLUDED_KEYS}

    def get_modified_keys_recursive(self) -> set:
        mod_keys = self.get_modified_keys()
        self.add_adjacent_keys(mod_keys)
        return mod_keys - {STAMPS_KEY, *CR_EXCLUDED_KEYS}

    def add_adjacent_keys(self, key_set):
        copy_set = set(key_set)  # we must copy the set so we can modify the real while while enumerating
        for key in copy_set:
            self._add_adjacent_keys(key, key_set)

    def _add_adjacent_keys(self, key: str, key_set: set):
        assert key in key_set, 'logic error'
        assert key in self, 'key is not in self??'

        # Get all keys modified in conjunction with 'key'
        new_keys = set()
        for contract_idx in self[key]['contracts']:
            new_keys = new_keys.union(self.writes[contract_idx])

        # Recursive stage
        for k in new_keys:
            if k in key_set:  # Base case -- if this key is already in the key_list do not recurse
                continue
            else:
                key_set.add(k)
                self._add_adjacent_keys(k, key_set)

    def reset_key(self, key):
        self.log.debugv("Resetting key {}".format(key))
        og_val = self[key]['og']

        self[key]['mod'] = None
        self[key]['contracts'] = set()

        if self.working.exists(key) and self.working.get(key) != og_val:
            self.log.debugv("Reseting key {} to COMMON value {}".format(key, self.working.get(key)))
            self[key]['og'] = self.working.get(key)
        elif self.master.exists(key) and self.master.get(key) != og_val:
            self.log.debugv("Reseting key {} to MASTER value {}".format(key, self.master.get(key)))
            self[key]['og'] = self.master.get(key)
        else:
            self.log.spam("No updated value found for key {}. Clearing modified and leaving original val".format(key))



