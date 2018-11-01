import redis
from seneca.logger.base import get_logger


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
    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, contract_idx: int,
                 finalize=False):
        self.log = get_logger("CRCmd-{}[sbb:{}][{}]".format(self.__name__, sbb_idx, contract_idx))
        self.finalize = finalize
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

        self._sbb_prefix = "sbb_{}:".format(sbb_idx)
        self._common_prefix = "common:"

    def _sbb_modified_key(self, key: str):
        return self._sbb_prefix + 'modified:' + key

    def _sbb_original_key(self, key: str):
        return self._sbb_prefix + 'original:' + key

    def _common_key(self, key: str):
        return self._common_prefix + key

    def execute(self, key, *args, **kwargs):
        raise NotImplementedError("execute must be implemented")


class CRGetSetBase(CRCommandBase):
    def _copy_og_key_if_not_exists(self, key):
        og_key = self._sbb_original_key(key)

        if not self.working_db.exists(og_key):
            # First check the common layer for the key
            common_key = self._common_key(key)
            if self.working_db.exists(common_key):
                val = self.working_db.get(common_key)
                self.log.debugv("Copying common key {} to sb specific original key {} with value {}"
                                .format(common_key, og_key, val))
                self.working_db.set(og_key, val)

            # Next, check the Master layer for the key
            if self.master_db.exists(key):
                val = self.master_db.get(key)
                self.log.debugv("Copying master key {} to sb specific original key {} with value {}"
                                .format(key, og_key, val))
                self.working_db.set(og_key, val)

            # If key not found in common or master layer, complain
            else:
                raise Exception("Key {} not found in Master or common layer!".format(key))


class CRGet(CRGetSetBase):
    COMMAND_NAME = 'get'

    def execute(self, key, *args, **kwargs):
        assert args is None, "CRGet not expected to be called with anything other than key! Args={}".format(args)
        assert kwargs is None, "CRGet not expected to be called with anything other than key! Args={}".format(kwargs)
        self._copy_og_key_if_not_exists(key)


class CRSet(CRGetSetBase):
    COMMAND_NAME = 'set'

    def execute(self, key, *args, **kwargs):
        assert args is None, "CRSet not expected to be called with anything other than key! Args={}".format(args)
        assert kwargs is None, "CRSet not expected to be called with anything other than key! Args={}".format(kwargs)
        self._copy_og_key_if_not_exists(key)           
