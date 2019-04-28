from ...logger import get_logger
from .conflict_resolution import CRContext, CR_EXCLUDED_KEYS

# TODO -- instead of passing in CRContext, we should be able to get away with just passing in
# the CRDataGetSet ....


class CRCmdBase:
    def __init__(self, working_db, master_db, contract_idx: int, data: CRContext):
        self.log = get_logger("{}[contract_{}]".format(type(self).__name__, contract_idx))
        self.data = data.cr_data
        self.working, self.master = working_db, master_db
        self.contract_idx = contract_idx

    def set_params(self, working_db, master_db, contract_idx: int, data: CRContext):
        self.data = data.cr_data
        self.working, self.master = working_db, master_db
        self.contract_idx = contract_idx

    def _copy_og_key_if_not_exists(self, key):
        """
        Copies the key from either master db or common layer (working db) to the sub-block specific layer, if it does
        not exist already
        """

        # debug
        # self.log.info("key {} and master is {}".format(key, self.master))
        # self.log.notice("master has keys:\n{}".format(self.master.keys()))
        # end debug

        # If the key already exists, bounce out of this method immediately
        if self._sbb_original_exists(key):
            self.log.spam("Key <{}> already exists in sub-block specific data, thus not recopying".format(key))
            return

        # First check the common layer for the key
        if self._db_original_exists(self.working, key):
            self.log.spam("Copying common key <{}> to sb specific data" .format(key))
            self._copy_key_to_sbb_data(self.working, key)

        # Next, check the Master layer for the key
        elif self._db_original_exists(self.master, key):
            self.log.spam("Copying master key <{}> to sb specific data" .format(key))
            self._copy_key_to_sbb_data(self.master, key)

        # Otherwise, if key not found in common or master layer, mark the original as None
        else:
            self.log.spam("Key {} not found in master layer. Defaulting original to None.".format(key))
            self._copy_key_to_sbb_data(None, key)

    def _db_original_exists(self, db, key) -> bool:
        """
        Returns True if 'key' exists on db. False otherwise. args/kwargs can be supplied for more complex
        implementations by subclasses
        :param db: The DB to check
        :param key: The key to check on 'db'
        """
        return db.exists(key)

    def _sbb_original_exists(self, key) -> bool:
        """
        Return True if key exists in the sub-block specific data, and False otherwise.
        """
        return key in self.data

    def _copy_key_to_sbb_data(self, db, key):
        """
        Copies 'key' from the specified to the sub-block specific data
        :param db: The DB to copy the key from. If None, it is implied that the key does not exist in common/master, and
        thus the original value will be set as None
        :param key: The name of the key to copy
        """
        val = db.get(key) if db else None
        self.data[key] = {'og': val, 'mod': None, 'contracts': set()}

    def _get(self, key):
        self._copy_og_key_if_not_exists(key)
        return self.data[key]['og']


class CRCmdGet(CRCmdBase):
    def __call__(self, key):
        return self._get(key)


class CRCmdSet(CRCmdBase):
    def _add_key_to_redo_log(self, key):
        # Return if key already exist in this contract's redo log
        if key in self.data.redo_log[self.contract_idx]:
            return

        self.data.redo_log[self.contract_idx][key] = self._get(key)
        self.log.spam("Contract {} added key {} to redo log with val {}".format(self.contract_idx, key,
                                                                                self.data.redo_log[
                                                                                self.contract_idx][key]))

    def __call__(self, key, value):
        # TODO properly handle CR on stamps key
        if key in CR_EXCLUDED_KEYS:
            return

        assert type(value) in (str, bytes), "Attempted to use 'set' with a value that is not str or bytes (val={}). " \
                                            "This is not supported currently.".format(value)
        self._copy_og_key_if_not_exists(key)
        if type(value) is str:
            value = value.encode()

        self._add_key_to_redo_log(key)

        self.log.spam("Setting SBB specific key <{}> to value {}".format(key, value))
        self.data[key]['mod'] = value
        self.data[key]['contracts'].add(self.contract_idx)
        self.data.writes[self.contract_idx].add(key)
        self.data.outputs[self.contract_idx] += 'SET {} {};'.format(key, value.decode())
