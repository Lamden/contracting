from ..logger import get_logger
from ..parallelism.conflict_resolution import CRContext
from ..parallelism.cr_commands import CRCmdGet, CRCmdSet


class CRDriver:

    def __init__(self, sbb_idx: int, contract_idx: int, data: CRContext):
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.log = get_logger("CRDriver")

        self.data = data

        # why does this guy need a reference of working and master db? can we do away with that
        # update -- i think its for convenience so we dont have to do data.master_db ... seems silly though...
        self.working_db, self.master_db = data.working_db, data.master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

        self.cmds = {'get': CRCmdGet(self.working_db, self.master_db, self.sbb_idx, self.contract_idx, self.data),
                     'set': CRCmdSet(self.working_db, self.master_db, self.sbb_idx, self.contract_idx, self.data)}

    def __getattr__(self, item):
        assert item in ('set', 'get'), "Only set and get supported by CRDriver, but got command: {}".format(item)

        cmd = self.cmds[item]
        cmd.set_params(working_db=self.working_db, master_db=self.master_db, sbb_idx=self.sbb_idx,
                       contract_idx=self.contract_idx, data=self.data)
        return cmd
