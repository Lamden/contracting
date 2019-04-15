import multiprocessing

#from seneca.parallelism import book_keeper, conflict_resolution
from seneca.execution import module, runtime

from seneca.db.driver import ContractDriver


class Executor:

    def __init__(self, metering=True, concurrency=True, flushall=False):
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
        self.tracer = None

        self.sandbox = SandboxBase()

    @property
    # Colin - I don't understand what this property is for, why
    #         do we need a driver_proxy for CR, we should not be
    #         instantiating drivers all over the place.
    def driver(self):
        if self.concurrency:
            if not self.driver_proxy:
                info = book_keeper.BookKeeper.get_cr_info()
                self.driver_proxy = conflict_resolution.StateProxy(sbb_idx=info['sbb_idx'], contract_idx=info['contract_idx'],
                                               data=info['data'])
            else:
                info = book_keeper.BookKeeper.get_cr_info()
                self.driver_proxy.sbb_idx = info['sbb_idx']
                self.driver_proxy.contract_idx = info['contract_idx']
                self.driver_proxy.data = info['data']
            return self.driver_proxy
        else:
            return self.driver_base

    def execute(self, sender, code_str):
        return self.sandbox.execute(sender, code_str)


class SandboxBase(object):
    def __init__(selfs):
        return

    def execute(self, sender, code_str):
        runtime.rt.ctx.pop()
        runtime.rt.ctx.append(sender)
        module = exec(code_str)
        return module


class Sandbox(multiprocessing.Process):
    """
    The Sandbox class is used as a execution sandbox for a transaction.

    I/O pattern:

        ------------                                  -----------
        | Executor |  ---> Transaction Bag (all) ---> | Sandbox |
        ------------                                  -----------
                                                           |
        ------------                                       v
        | Executor |  <---      Send Results     <---  Execute all tx
        ------------

        * The client sends the whole transaction bag to the Sandbox for
          processing. This is done to minimize back/forth I/O overhead
          and deadlocks
        * The sandbox executes all of the transactions one by one, resetting
          the syspath after each execution.
        * After all execution is complete, pass the full set of results
          back to the client again to minimize I/O overhead and deadlocks
        * Sandbox blocks on pipe again for new bag of transactions
    """
    def __init__(self, pipe, **kwargs):
        super(Sandbox, self).__init__()
        self._kwargs = kwargs
        self._p_out, self._p_in = pipe

    def _execute(self, bag):
        """
        Execute a bag of transactions

        :param bag: A bag of transactions
        :return:
        """
        return

    def run(self, looptimeout=5):
        """

        :param looptimeout: Timeout in seconds to block on the queue. This is
                            here to prevent deadlocks
        :return:
        """
        while True:
            bag = self._p_in.recv()
            self._execute(bag)