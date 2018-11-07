import redis
from seneca.libs.logger import get_logger
from seneca.engine.conflict_resolution import CRDataGetSet, CRDataContainer, CRDataBase


class CRCmdMeta(type):
    def __new__(cls, clsname, bases, clsdict):
        clsobj = super().__new__(cls, clsname, bases, clsdict)
        if not hasattr(clsobj, 'registry'):
            clsobj.registry = {}

        if 'COMMAND_NAME' in clsdict:
            cmd_name = clsdict['COMMAND_NAME']
            assert cmd_name not in clsobj.registry, "Command {} already in registry {}".format(cmd_name, clsobj.registry)
            clsobj.registry[cmd_name] = clsobj

        return clsobj


class CRCmdBase(metaclass=CRCmdMeta):
    DATA_NAME = None

    # TODO -- remove the finalize var. We dont need this.
    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, contract_idx: int,
                 data: CRDataContainer, finalize=False):
        self.log = get_logger("{}[sbb_{}][contract_{}]".format(type(self).__name__, sbb_idx, contract_idx))
        self.finalize = finalize
        self.data = data
        self.working, self.master = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

    def _copy_og_key_if_not_exists(self, key, *args, **kwargs):
        """
        Copies the key from either master db or common layer (working db) to the sub-block specific layer, if it does
        not exist already
        """
        # If the key already exists, bounce out of this method immediately
        if self._sbb_original_exists(key, *args, **kwargs):
            self.log.debugv("Key <{}> already exists in sub-block specific data, thus not recopying".format(key))
            return

        # First check the common layer for the key
        if self._db_original_exists(self.working, key, *args, **kwargs):
            self.log.debugv("Copying common key <{}> to sb specific data" .format(key))
            self._copy_key_to_sbb_data(self.working, key, *args, **kwargs)

        # Next, check the Master layer for the key
        elif self._db_original_exists(self.master, key, *args, **kwargs):
            self.log.debugv("Copying master key <{}> to sb specific data" .format(key))
            # type(self)._write(self.working, og_key, val)
            self._copy_key_to_sbb_data(self.master, key, *args, **kwargs)

        # Otherwise, if key not found in common or master layer, mark the original as None
        else:
            self._copy_key_to_sbb_data(None, key, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def _db_original_exists(self, db: redis.StrictRedis, key: str, *args, **kwargs) -> bool:
        """
        Returns True if 'key' exists on db. False otherwise. args/kwargs can be supplied for more complex
        implementations by subclasses
        :param db: The DB to check
        :param key: The key to check on 'db'
        """
        raise NotImplementedError()

    def _sbb_original_exists(self, key, *args, **kwargs) -> bool:
        """
        Return True if key exists in the sub-block specific data, and False otherwise.
        """
        raise NotImplementedError()

    def _copy_key_to_sbb_data(self, db: redis.StrictRedis or None, key: str, *args, **kwargs):
        """
        Copies 'key' from the specified to the sub-block specific data
        :param db: The DB to copy the key from. If None, it is implied that the key does not exist in common/master, and
        thus the original value will be set as None
        :param key: The name of the key to copy
        """
        raise NotImplementedError()


class CRCmdExists(CRCmdBase):
    COMMAND_NAME = 'exists'

    def __call__(self, key):
        # TODO this could be made more modular. Current implementation will not scale well --davis
        # First check if key exists in getset
        if key in self.data['getset']:
            return True
        # Next check if key is in HMap
        if key in self.data['hm']:
            return True
        # Then check if it exists in the common layer...
        if self.working.exists(key):
            return True
        # Then finally, check if it exists in the master layer
        return self.master.exists(key)


class CRCmdGetSetBase(CRCmdBase):
    DATA_NAME = 'getset'

    def _db_original_exists(self, db: redis.StrictRedis, key: str) -> bool:
        return db.exists(key)

    def _sbb_original_exists(self, key) -> bool:
        return key in self.data['getset']

    def _copy_key_to_sbb_data(self, db: redis.StrictRedis, key: str):
        val = db.get(key) if db else None
        self.data['getset'][key] = {'og': val, 'mod': None}


class CRCmdGet(CRCmdGetSetBase):
    COMMAND_NAME = 'get'

    def __call__(self, key):
        self._copy_og_key_if_not_exists(key)

        # TODO make all this DRYer so you can abstract it like a pro

        # First, try and return the local modified key
        mod_val = self.data['getset'][key]['mod']
        if mod_val is not None:
            self.log.debugv("SBB specific MODIFIED key found for key named <{}>".format(key))
        # Otherwise, default to the local original key
        else:
            self.log.debugv("SBB specific ORIGINAL key found for key named <{}>".format(key))
            mod_val = self.data['getset'][key]['og']

        self.data['getset'].reads[self.contract_idx].add(key)
        return mod_val


class CRCmdSet(CRCmdGetSetBase):
    COMMAND_NAME = 'set'

    def __call__(self, key: str, value):
        assert type(value) in (str, bytes), "Attempted to use 'set' with a value that is not str or bytes (val={}). " \
                                            "This is not supported currently.".format(value)
        self._copy_og_key_if_not_exists(key)
        if type(value) is str:
            value = value.encode()

        self.log.debugv("Setting SBB specific key <{}> to value {}".format(key, value))
        self.data['getset'][key]['mod'] = value

        self.data['getset'].writes[self.contract_idx].add(key)


class CRCmdHMapBase(CRCmdBase):
    # MOD_DELIM is used to delimeter the 'key' and 'field' for storing key-fields in the modifications list
    # (key is the name of the hash table, and field is the field on that hash table)
    # TODO this sketches me out. Can people name their keys in such a way that they can do 'sql injection like' attacks?  -- davis
    MOD_DELIM = '*-*'
    DATA_NAME = 'hm'

    def _db_original_exists(self, db: redis.StrictRedis, key: str, field: str) -> bool:
        return db.hexists(key, field)

    def _sbb_original_exists(self, key: str, field: str) -> bool:
        return key in self.data['hm'] and field in self.data['hm'][key]

    def _copy_key_to_sbb_data(self, db: redis.StrictRedis, key: str, field: str):
        val = db.hget(key, field) if db else None
        self.data['hm'][key][field] = {'og': val, 'mod': None}

    def _get_key_field_name(self, key: str, field: str):
        return key + self.MOD_DELIM + field


class CRCmdHGet(CRCmdHMapBase):
    COMMAND_NAME = 'hget'

    def __call__(self, key, field):
        self._copy_og_key_if_not_exists(key, field)

        # TODO make all this DRYer so you can abstract like a pro

        # First, try and return the local modified key
        mod_val = self.data['hm'][key][field]['mod']
        if mod_val is not None:
            self.log.debugv("SBB specific MODIFIED key found for key named <{}>".format(key))
            return mod_val

        # Otherwise, default to the local original key
        self.log.debugv("SBB specific ORIGINAL key found for key named <{}>".format(key))
        return self.data['hm'][key][field]['og']
        # TODO add the read list


class CRCmdHSet(CRCmdHMapBase):
    COMMAND_NAME = 'hset'

    def __call__(self, key: str, field: str, value):
        assert type(value) in (str, bytes), "Attempted to use 'hset' with a value that is not str or bytes (val={}). " \
                                            "This is not supported currently.".format(value)
        self._copy_og_key_if_not_exists(key, field)
        if type(value) is str:
            value = value.encode()

        self.log.debugv("Setting SBB specific key <{}> to value {}".format(key, value))
        self.data['hm'][key][field]['mod'] = value

        # self._add_key_to_mod_list(self._get_key_field_name(key, field))
        # TODO add the write list

