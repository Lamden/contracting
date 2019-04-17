import multiprocessing
import importlib

from seneca.parallelism import book_keeper, cr_driver
from seneca.execution import runtime
from seneca.db import driver


class Executor:

    def __init__(self, metering=True, concurrency=True, flushall=False, production=False):
        # Colin - Load in the database driver from the global config
        #         Set driver_proxy to none to indicate it exists and
        #         may be filled later
        self.driver_base = driver.ContractDriver()
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

        if production:
            self.sandbox = MultiProcessingSandbox()
        else:
            self.sandbox = Sandbox()

    @property
    # Colin - I don't understand what this property is for, why
    #         do we need a driver_proxy for CR, we should not be
    #         instantiating drivers all over the place.
    def driver(self):
        if self.concurrency:
            if not self.driver_proxy:
                info = book_keeper.BookKeeper.get_cr_info()
                self.driver_proxy = cr_driver.CRDriver(sbb_idx=info['sbb_idx'], contract_idx=info['contract_idx'],
                                                       data=info['data'])
            else:
                info = book_keeper.BookKeeper.get_cr_info()
                self.driver_proxy.sbb_idx = info['sbb_idx']
                self.driver_proxy.contract_idx = info['contract_idx']
                self.driver_proxy.data = info['data']
            return self.driver_proxy
        else:
            return self.driver_base

    def execute_bag(self, bag):
        """
        The execute bag method sends a list of transactions to the sandbox to be executed

        :param bag: a list of deserialized transaction objects
        :return: a list of results (result index == bag index), formatted as
                 [ (status_code, result), ... ] where status_code is 0 or 1
                 depending on success/failure and result is what is returned
                 from executing the underlying function
        """
        results = []
        for tx in bag:
            sender = tx.sender
            contract_name = tx.contractName
            function_name = tx.functionName
            kwargs = tx.kwargs
            # TODO: Need to interpret the required code_str using Seneca bindings from the contents of tx
            results.append(self.execute(sender, contract_name, function_name, kwargs))
        return results

    def execute(self, sender, contract_name, function_name, kwargs):
        """
        Method that does a naive execute

        :param sender:
        :param contract_name:
        :param function_name:
        :param kwargs:
        :return: result of execute call
        """
        # A successful run is determined by if the sandbox execute command successfully runs.
        # Therefor we need to have a try catch to communicate success/fail back to the
        # client. Necessary in the case of batch run through bags where we still want to
        # continue execution in the case of failure of one of the transactions.
        try:
            result = self.sandbox.execute(sender, contract_name, function_name, kwargs)
            status_code = 0
        # TODO: catch SenecaExceptions distinctly, this is pending on Raghu looking into Exception override in compiler
        except Exception as e:
            result = e
            status_code = 1
        return status_code, result


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


class Sandbox:
    def __init__(self):
        pass

    def execute(self, sender, contract_name, function_name, kwargs):
        runtime.rt.ctx.pop()
        runtime.rt.ctx.append(sender)

        module = importlib.import_module(contract_name)
        func = getattr(module, function_name)

        return func(**kwargs)


class MultiProcessingSandbox(Sandbox):
    def __init__(self):
        self.pipe = multiprocessing.Pipe()
        self.p = None

    def terminate(self):
        if self.p:
            self.p.terminate()

    def execute(self, sender, contract_name, function_name, kwargs):
        if self.p is None:
            self.p = multiprocessing.Process(target=self.process_loop,
                                             args=(super().execute, ))
            self.p.start()

        _, child_pipe = self.pipe

        # Sends code to be executed in the process loop
        child_pipe.send((sender, contract_name, function_name, kwargs))

        # Receive result object back from process loop, formatted as
        # (status_code, result), loaded in using dill due to python
        # base pickler not knowning how to pickle module object
        # returned from execute
        status_code, result = child_pipe.recv()

        # Check the status code for failure, if failure raise the result
        if status_code > 0:
            raise result
        return result

    def process_loop(self, execute_fn):
        parent_pipe, _ = self.pipe
        while True:
            sender, contract_name, function_name, kwargs = parent_pipe.recv()
            try:
                result = execute_fn(sender, contract_name, function_name, kwargs)
                status_code = 0
            except Exception as e:
                result = e
                status_code = 1
            finally:
                # Pickle the result using dill so module object can be retained
                parent_pipe.send((status_code, result))
