from seneca.db.cr.conflict_resolution import CRContext
from typing import List
from ...logger import get_logger

from transitions import Machine


class TransactionBag:
    def __init__(self, transactions: List[tuple], cr_context: CRContext):
        self.cr_context = cr_context
        self.transactions = sorted(transactions, key=lambda x: x[0])

    def __iter__(self):
        for t in self.transactions:
            yield t

    # ideally we should have designed the bag to do this in O(1) but w/e yolo imma just b search that shit
    def get_tx_at_idx(self, idx: int):
        i, j = 0, len(self.transactions) - 1

        while j >= i:
            mid = (i+j) // 2
            if self.transactions[mid][0] == idx:
                return self.transactions[mid][1]
            elif self.transactions[mid][0] > idx:
                j = mid-1
            else:
                i = mid+1

        raise Exception("No transaction found in bag with index {}! Bag's transactions: {}"
                        .format(idx, self.transactions))


class TransactionBag:


    def __init__(self, common_db: CRDriver, master_db: CRDriver, transactions: list):
        self.log = get_logger(type(self).__name__)
        
        self.common = common_db
        self.master = master_db

        self.transactions = {k: v for k, v in enumerate(transactions)}
        self.toYield = transactions.keys()

        # Setup the state machine

        # TODO deques are probobly more optimal than using arrays here
        # run_results is a list of strings, representing the return code of contracts (ie 'SUCC', 'FAIL', ..)
        self.run_results = []
        self.contracts = []  # A list of ContractionTransaction objects. SenecaClient should append as it runs contracts
        self.input_hash = None  # Input hash should be set by SBBClient once a new sub block is started
        
        self.merged_to_common = False

    def setup_reruns(self):
        #TODO: check for reruns
        self.toYield = []

    def __iter__(self):

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
        assert len(self.contracts) > contract_idx, "contract_idx {} out of bounds. Only {} contracts in self.contracts" \
            .format(contract_idx, len(self.contracts))
        self.log.debugv("Updating run result for contract idx {} to <{}>".format(contract_idx, result))
        self.run_results[contract_idx] = result

    def rollback_contract(self, contract_idx: int):
        # TODO this only works for set/get
        self.cr_data['getset'].rollback_contract(contract_idx)

    def reset_run_data(self):
        """ Resets all state held by this container. """
        self.log.debug("Resetting run data for CRData with ".format(self.input_hash, id(self)))

        # Reset this object's state
        self.run_results.clear()
        self.contracts.clear()
        self.merged_to_common = False
        self.input_hash = None

        # TODO is this ok resetting all the CRData's like this? Should we worry about memory leaks? --davis
        self.cr_data = CRDataGetSet(self.master, self.common)

    def reset_db(self):
        self.log.debug(
            "CRData resetting working db #{}".format(self.common.connection_pool.connection_kwargs['db']))
        self.common.flushdb()

    def assert_reset(self):
        """ Assert this object has been reset_db properly. For dev purposes. """

        old_locked_val = self.locked
        self.locked = False

        err = "\nContracts: {}\nRun Results: {}\nWrites: {}\nOutputs: {}\nRedo Log: {}\nInput hash: {}\n" \
            .format(self.contracts, self.run_results, self.cr_data.writes,
                    self.cr_data.outputs, self.cr_data.redo_log, self.input_hash)
        assert len(self.contracts) == 0, err
        assert len(self.run_results) == 0
        assert len(self.cr_data.writes) == 0, err
        assert len(self.cr_data.outputs) == 0, err
        assert len(self.cr_data.redo_log) == 0, err
        assert not self.merged_to_common
        assert self.input_hash is None, "Input hash not reset. (self.input_hash={})".format(self.input_hash)

        self.locked = old_locked_val

    def get_state_for_idx(self, contract_idx: int) -> str:
        """
        Returns the state for the contract at the specified index
        """
        assert contract_idx < len(self.contracts), "Contract index {} out of bounds for self.contracts of length {}" \
            .format(contract_idx, len(self.contracts))

        state_str = ''
        state_str += self.cr_data.get_state_for_idx(contract_idx)
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

    def iter_rerun_indexes(self):
        # TODO this only works for getset right now
        # TODO this does not support new keys being modified during the rerun process
        data = self.cr_data['getset']
        contract_list = data.get_rerun_list()
        self.log.info("Contracts indexes to rerun: {}".format(contract_list))

        # DEBUG -- TODO DELETE
        # self.log.notice("CRData with input hash {}".format(self.input_hash))
        # self.log.notice("CRData with id {}".format(id(self)))
        # self.log.notice("CRData contracts length: {}".format(len(self.contracts)))
        # self.log.info("data reads: {}".format(data.reads))
        # self.log.info("data writes: {}".format(data.writes))
        # END DEBUG

        for i in contract_list:
            self.log.debugv("Rerunning contract at index {}".format(i))
            og_reads, og_writes = data.reads[i], data.writes[i]
            self.reset_contract_data(i)

            yield i

            # TODO handle this behavior by reverting and failing until we have a better mechanism
            assert og_reads == data.reads[i], "Original reads have changed for contract idx {}!\nOriginal: {}\nNew " \
                                              "Reads: {}".format(i, og_reads, data.reads[i])
            assert og_writes == data.writes[i], "Original writes have changed for contract idx {}!\nOriginal: {}\nNew " \
                                                "Writes: {}".format(i, og_writes, data.writes[i])

    def reset_contract_data(self, contract_idx: int):
        """
        Resets the reads list and modification list for the contract at index idx.
        """
        for obj in self.cr_data.values():
            obj.reset_contract_data(contract_idx)

    def merge_to_common(self):
        assert not self.merged_to_common, "Already merged to common! merge_to_common should only be called once"
        self.cr_data.merge_to_common()
        self.merged_to_common = True

    # Why is this a class method?
    @classmethod
    def merge_to_master(cls, common, master):
        from seneca.db.cr.client import Macros  # to avoid cyclic imports
        keys = common.keys()
        for key in keys:
            # Ignore Phase keys
            if key in Macros.ALL_MACROS:
                continue

            CRDataGetSet.merge_to_master(common, master, key)

    def __repr__(self):
        return "<CRContext(input_hash={} .., contracts run so far={}, working db num={})>".format(
            self.input_hash[:16], len(self.contracts), self.working_db.connection_pool.connection_kwargs['db'])

