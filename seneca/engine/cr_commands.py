import redis
from seneca.libs.logger import get_logger


class CRCommandMeta(type):
    def __new__(cls, clsname, bases, clsdict):
        clsobj = super().__new__(cls, clsname, bases, clsdict)
        if not hasattr(clsobj, 'registry'):
            clsobj.registry = {}

        if 'COMMAND_NAME' in clsdict:
            # assert 'COMMAND_NAME' in clsdict, 'COMMAND_NAME not set in CRCommand subclass {}'.format(clsname)
            cmd_name = clsdict['COMMAND_NAME']
            assert cmd_name not in clsobj.registry, "Command {} already in registry {}".format(cmd_name, clsobj.registry)

            clsobj.registry[cmd_name] = clsobj

        return clsobj


class CRCommandBase(metaclass=CRCommandMeta):
    MODS_LIST_DELIM = '***'

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, contract_idx: int,
                 finalize=False):
        self.log = get_logger("{}[sbb_{}][contract_{}]".format(type(self).__name__, sbb_idx, contract_idx))
        self.finalize = finalize
        self.working, self.master = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

        self._sbb_prefix = "sbb_{}:".format(sbb_idx)
        self._common_prefix = "common:"
        self._mods_list_key = self._mods_list_key(sbb_idx)

    @classmethod
    def get_mods_for_sbb_idx(cls, sbb_idx: int, db: redis.StrictRedis) -> list:
        """
        Gets a list of all modifications for a particular sub block. Returns a list of lists, where each nested list
        i represents a list of keys modified by contract i.
        For example:
        [[key1, key2], [key3], [key2], ...]
        can be interpreter as contract 0 modifying (key1, key2), contract 1 modifying (key3), ect ect
        """
        # TODO -- optimize modification list storage
        # this is O(n + m). where n is total contracts in this block, and m is avg # of mod keys per contract.
        # Feels very inefficient. Is there a more optimal approach? --davis
        mod_list_key = cls._mods_list_key(sbb_idx)
        all_mods = []
        for i in range(db.llen(mod_list_key)):
            mods_str = db.lindex(mod_list_key, i).decode()
            all_mods.append(mods_str.split(cls.MODS_LIST_DELIM))

        return all_mods

    def _add_key_to_mod_list(self, key: str):
        self.log.spam("Adding key <{}> to modification list".format(key))

        # Push a new element onto the list of a string of modifications does not exists yet for this contract
        if self.working.llen(self._mods_list_key) <= self.contract_idx:
            self.log.debugv("Pushing a new element onto modification list for key <{}>".format(key))
            self.working.rpush(self._mods_list_key, key)

        # Otherwise, we need to append it to current list of modifications for this contract
        else:
            mods = self.working.lindex(self._mods_list_key, self.contract_idx).decode()

            # Do not record this key if it is already in the list of modifications
            if key in mods:
                self.log.debugv("Key <{}> already in existing mods <{}>. Skipping.".format(key, mods))
                return

            self.log.debugv("Adding mod key <{}> to existing mods <{}>".format(key, mods))
            mods += self.MODS_LIST_DELIM + key
            self.working.lset(self._mods_list_key, self.contract_idx, mods)

        # Development sanity check. This should NEVER happen (we should be executing contracts sequentially per sbb).
        # In other words, we should always be adding to the mod list of the latest contract, not a prior one
        assert self.working.llen(self._mods_list_key) == self.contract_idx + 1, \
            "DEVELOPER LOGIC ERROR!!! Contract idx {} does not match modifications list of length {}"\
            .format(self.contract_idx, self.working.llen(self._mods_list_key))

    def _copy_og_key_if_not_exists(self, key):
        og_key = self._sbb_original_key(key)

        if not self.working.exists(og_key):
            # First check the common layer for the key
            common_key = self._common_key(key)
            if self.working.exists(common_key):
                val = self.working.get(common_key)
                self.log.debugv("Copying common key <{}> to sb specific original key <{}> with value <{}>"
                                .format(common_key, og_key, val))
                self.working.set(og_key, val)

            # Next, check the Master layer for the key
            if self.master.exists(key):
                val = self.master.get(key)
                self.log.debugv("Copying master key <{}> to sb specific original key <{}> with value <{}>"
                                .format(key, og_key, val))
                self.working.set(og_key, val)

            # Otherwise, if key not found in common or master layer, complain
            else:
                raise Exception("Key <{}> not found in Master or common layer!".format(key))

    @classmethod
    def _mods_list_key(cls, sbb_idx):
        return "sbb_{}_modifications".format(sbb_idx)

    def _sbb_modified_key(self, key: str):
        return self._sbb_prefix + 'modified:' + key

    def _sbb_original_key(self, key: str):
        return self._sbb_prefix + 'original:' + key

    def _common_key(self, key: str):
        return self._common_prefix + key

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("__call__ must be implemented")

    def read(self, key, *args, **kwargs):
        raise NotImplementedError()

    def write(self, key, value, *args, **kwargs):
        raise NotImplementedError()

class CRGetSetBase(CRCommandBase):
    def _copy_og_key_if_not_exists(self, key):
        og_key = self._sbb_original_key(key)

        if not self.working.exists(og_key):
            # First check the common layer for the key
            common_key = self._common_key(key)
            if self.working.exists(common_key):
                val = self.working.get(common_key)
                self.log.debugv("Copying common key <{}> to sb specific original key <{}> with value <{}>"
                                .format(common_key, og_key, val))
                self.working.set(og_key, val)

            # Next, check the Master layer for the key
            elif self.master.exists(key):
                val = self.master.get(key)
                self.log.debugv("Copying master key <{}> to sb specific original key <{}> with value <{}>"
                                .format(key, og_key, val))
                self.working.set(og_key, val)

            # Otherwise, if key not found in common or master layer, complain
            else:
                raise Exception("Key <{}> not found in Master or common layer!".format(key))


class CRGet(CRGetSetBase):
    COMMAND_NAME = 'get'

    def __call__(self, key, *args, **kwargs):
        assert len(args) == 0, "CRGet not expected to be called with anything other than key! Args={}".format(args)
        assert len(kwargs) == 0, "CRGet not expected to be called with anything other than key! Args={}".format(kwargs)
        self._copy_og_key_if_not_exists(key)

        # First, try and return the local modified (sbb specific) key
        mod_key = self._sbb_modified_key(key)
        if self.working.exists(mod_key):
            self.log.debugv("SBB specific MODIFIED key <{}> found for key named <{}>".format(mod_key, key))
            return self.working.get(mod_key)

        # Otherwise, default to the local original key
        og_key = self._sbb_original_key(key)
        if self.working.exists(og_key):
            self.log.debugv("SBB specific ORIGINAL key <{}> found for key named <{}>".format(og_key, key))
            return self.working.get(og_key)

        # TODO does phase 2 require special logic?


class CRSet(CRGetSetBase):
    COMMAND_NAME = 'set'

    def __call__(self, key, value, *args, **kwargs):
        assert len(args) == 0, "CRSet not expected to be called with anything other than key! Args={}".format(args)
        assert len(kwargs) == 0, "CRSet not expected to be called with anything other than key! Args={}".format(kwargs)
        self._copy_og_key_if_not_exists(key)

        # TODO does phase 2 require special logic?

        # Set modified key
        mod_key = self._sbb_modified_key(key)
        self.working.set(mod_key, value)

        self._add_key_to_mod_list(key)


