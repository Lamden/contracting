from seneca.execution.parser import Parser
from seneca.execution.scope import Scope
#from seneca.metering.tracer import Tracer
from seneca.config import CODE_OBJ_MAX_CACHE, READ_ONLY_MODE
import types
import threading
from os.path import join
from functools import lru_cache
from seneca.utils import Plugins, Assert
from seneca.parallelism.book_keeper import BookKeeper
from seneca.parallelism.conflict_resolution import StateProxy
from seneca.db.driver import ContractDriver


class Executor:

    def __init__(self, metering=True, concurrency=True, flushall=False):
        # Colin - Ensure everything is nuked down to minimal viable set
        #         before we start doing ANYTHING
        # uninstall_builtins()
        #
        # # Colin - Put the database loader in the sys path
        # install_database_loader()

        # Colin - Load in the database driver from the global config
        #         Set driver_proxy to none to indicate it exists and
        #         may be filled later
        self.driver_base = ContractDriver()
        self.driver_proxy = None
        if flushall:
            self.driver.flush()

        # Colin - Load in the parameters for the default contracts
        #         NOTE: Not sure this belongs here at all (should
        #               be happening in bootstrap most likely).
        #self.path = join(seneca.__path__[0], 'contracts')
        #self.author = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
        #self.official_contracts = OFFICIAL_CONTRACTS
        #self.setup_official_contracts()

        # Setup whether or not flags have been set
        self.metering = metering
        self.concurrency = concurrency

        # Colin -  Setup the tracer
        # Colin TODO: Find out why Tracer is not instantiating properly. Raghu also said he wants to pull this out.
        #cu_cost_fname = join(seneca.__path__[0], 'constants', 'cu_costs.const')
        #self.tracer = Tracer(cu_cost_fname)
        #Plugins.submit_stamps()

    @property
    # Colin - I don't understand what this property is for, why
    #         do we need a driver_proxy for CR, we should not be
    #         instantiating drivers all over the place.
    def driver(self):
        if self.concurrency:
            if not self.driver_proxy:
                info = BookKeeper.get_cr_info()
                self.driver_proxy = CRDriver(sbb_idx=info['sbb_idx'], contract_idx=info['contract_idx'],
                                               data=info['data'])
            else:
                info = BookKeeper.get_cr_info()
                self.driver_proxy.sbb_idx = info['sbb_idx']
                self.driver_proxy.contract_idx = info['contract_idx']
                self.driver_proxy.data = info['data']
            return self.driver_proxy
        else:
            return self.driver_base

    # Colin - This should not be happening here. If we want to use
    #         the Executor class in multiple locations (multiple
    #         instantiations) we cannot be setting up official
    #         contracts every time. This should be moved to system
    #         bootstrap method
    # Colin TODO: Move to boostrap.py to ensure we are 1-to-1 with boot not instance of executor

    def mock_execute(self):
        from types import ModuleType
        ctx = ModuleType('ctx')
        ctx.sender = 'test'

class Sandbox(object):
    """
    The Sandbox class is used as a execution sandbox for a transaction.
    This class is in control of the Sandbox Process
    """
    def __init__(self):
        return

    def communicate(self):
        """
        Method for communicating with the underlying SandboxThread(s).

        :return:
        """
        return

    def launch(self):
        """
        Method for launching underlying SandboxThread(s).

        :return:
        """
        return


class SandboxThread(threading.Thread):
    """
    The SandboxThread class is used as a thread inside the Sandbox
    handling the execution. It is leveraged to ensure execution inside
    a clean stack.
    """
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        """
        Method called when SandboxThread.start() is called. Runtime
        operations of the thread.

        :return:
        """
        return
