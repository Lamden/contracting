from collections import deque
import time, asyncio, ujson as json, redis
from seneca.libs.logger import get_logger
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter
from seneca.engine.util import make_n_tup
from seneca.constants.redis_config import *
from seneca.engine.conflict_resolution import CRDataContainer
from seneca.engine.book_keeper import BookKeeper

class Macros:
    EXECUTION = '_execution'
    CONFLICT_RESOLUTION = '_conflict_resolution'

    ALL_MACROS = [EXECUTION, CONFLICT_RESOLUTION]

class Phase:
    @staticmethod
    def reset_phase_variables(db):
        db.set(Macros.EXECUTION, 0)
        db.set(Macros.CONFLICT_RESOLUTION, 0)

    @staticmethod
    def incr_phase_variable(db, key):
        db.incr(key)

    @staticmethod
    def get_phase_variable(db, key):
        return db.get(key)


class SenecaClient(SenecaInterface):

    def __init__(self, sbb_idx, num_sbb, concurrent_mode=True, loop=None):

        super().__init__()

        name = self.__class__.__name__ + "[{}]".format(sbb_idx)
        self.log = get_logger(name)
        self.loop = loop or asyncio.get_event_loop()

        self.port = get_redis_port()
        self.password = get_redis_password()

        self.sbb_idx = sbb_idx
        self.num_sb_builders = num_sbb
        self.concurrent_mode = concurrent_mode

        self.curr_contract_idx = 0
        self.contract_queue = deque()

        self.master_db = None
        self.available_dbs = []
        self.pending_dbs = []
        self.active_db = None
        self.transaction_keys = []

        self.max_number_workers = NUM_CACHES

        self.setup_dbs()

    def setup_dbs(self):
        self.master_db = redis.StrictRedis(host='localhost', port=self.port, db=MASTER_DB, password=self.password)
        for db_num in range(self.max_number_workers):
            db_client = redis.StrictRedis(host='localhost', port=self.port, db=db_num+DB_OFFSET, password=self.password)
            cr_data = CRDataContainer(working_db=db_client, master_db=self.master_db, sbb_idx=self.sbb_idx)
            self.available_dbs.append(cr_data)
        self.active_db = self.available_dbs.pop()

    def reset_cr_data(self, ds: CRDataContainer):
        ds.reset()
        Phase.reset_phase_variables(ds.working_db)

    def update_master_db(self, from_db):
        assert Phase.get_phase_variable(from_db, Macros.CONFLICT_RESOLUTION) == self.num_sb_builders
        self.synchronize_phase(from_db, Macros.CONFLICT_RESOLUTION)
        # TODO from from_db, get each k,v and update the corresponding entries in master_db
        pass

    def flush(self, input_hash=None, result_hash=None, update_state=True):
        """
        If update_state is True, this will also commit the changes
        to the database. Otherwise, this method will discard any changes
        """
        raise NotImplementedError()
        # f_db = self.pending_dbs.pop(0)
        # if self.sbb_index == 0: # only one will do merging db work for now (but it could be the one that is not reponsible for sb)
        #     if update_state:
        #         # TODO make sure f_db is the one by matching input_hash(es) ?
        #         self.update_master_db(f_db)
        #     self.reset_db(f_db)
        # self.worker_dbs.append(f_db)

    def submit_contract(self, contract):
        self.publish_code_str(contract.contract_name, contract.sender, contract.code, keep_original=True, scope={
            'rt': make_n_tup({
                'author': contract.sender,
                'sender': contract.sender
            })
        })

    def run_contract(self, contract):
        BookKeeper.set_info(sbb_idx=self.sbb_idx, contract_idx=self.curr_contract_idx, data=self.active_db)

        contract_name = contract.contract_name
        metadata = self.get_contract_meta(contract_name)

        try:
            self.execute_code_str(contract.code, scope={
                'rt': make_n_tup({
                    'author': metadata['author'],
                    'sender': contract.sender
                })
            })
            result = 'SUCC'
        except Exception as e:
            self.log.warning("Contract failed with error: {} \ncontract obj: {}".format(e, contract))
            # TODO can we get more specific fail messages?
            result = 'FAIL' + ' -- ' + str(e)

        self.active_db.update_contract_result(self.curr_contract_idx, result)
        self.curr_contract_idx += 1

    def catchup(self):
        pass

    def start_sub_block(self):
        # TODO add input-bag hash (for use in catchup logic)
        if len(self.available_dbs) == 0:
            raise Exception("Attempted to start a new sub block, but there are no available DBs!")

        self.active_db = self.available_dbs.pop(0)

    def end_sub_block(self):
        Phase.incr_phase_variable(self.active_db, Macros.EXECUTION)
        self.pending_dbs.append(self.active_db)
        self.active_db = None  # we really don't care, but might be useful initially for error checking

    def get_next_sub_block(self):
        f_db = self.pending_dbs[0]  # get the first one, but still leave it in the pending_dbs too
        assert Phase.get_phase_variable(f_db, Macros.EXECUTION) == self.num_sb_builders
        self.synchronize_phase(f_db, Macros.EXECUTION)
        self.wait_my_turn(f_db, Macros.CONFLICT_RESOLUTION)
        txns = self.merge_sub_block(f_db)
        Phase.incr_phase_variable(self.f_db, Macros.CONFLICT_RESOLUTION)
        return txns

    def merge_sub_block(self, db):
        pass
        # for ord_no, list_obj in enumerate(self.get_order_key_lists(db)):
        #     key_list, sbb_index = list_obj['keys'], list_obj['idx']
        #     modified = False
        #     for key in key_list:
        #         orig_value = db.hget(Macros.COMMON, key)['ori']
        #         sbb_orig_value = db.hget(self.executed_key, key)['ori']
        #         if sbb_orig_value != orig_value:
        #             modified = True
        #             db.hset(self.executed_key, key, orig_value)
        #     if modified:
        #         pass
        #         # self.run_contract(contract)
        #     for key in key_list:
        #         mod_value = db.hget(self.executed_key, key)['mod']
        #         db.hset(Macros.COMMON, key, mod_value)

    def synchronize_phase(self, db, key):
        """
        Blocks until the db with key {}
        :return:
        """
        while Phase.get_phase_variable(db, key) < self.num_sb_builders:
            time.sleep(1) # TODO use better logic here

    def wait_my_turn(self, db, key):
        while Phase.get_phase_variable(db, key) < self.sbb_index:
            time.sleep(1) # TODO use better logic here
        assert Phase.get_phase_variable(db, key) == self.sbb_index
