import importlib
import multiprocessing
from typing import Dict

from . import runtime
from ..db.cr.transaction_bag import TransactionBag
from ..db.driver import ContractDriver, CacheDriver
from ..execution.module import install_database_loader


class Executor:

    def __init__(self, metering=True, production=False):
        self.metering = metering

        # Colin -  Setup the tracer
        # Colin TODO: Find out why Tracer is not instantiating properly. Raghu also said he wants to pull this out.
        #cu_cost_fname = join(contracting.__path__[0], 'constants', 'cu_costs.const')
        #self.tracer = Tracer(cu_cost_fname)

        self.tracer = None
        self.driver = ContractDriver()

        if production:
            self.sandbox = MultiProcessingSandbox()
        else:
            self.sandbox = Sandbox()

    def execute_bag(self, bag: TransactionBag, driver=None) -> Dict[int, tuple]:
        """
        The execute bag method sends a list of transactions to the sandbox to be executed
        In the case of bag execution the

        :param bag: a list of deserialized transaction objects
        :return: A dictionary with transaction index as the key and execution result
                 objects as the value. Formatted as follows:

                 {
                    1: (0, 'balance=10')
                    2: (1, ImportError)
                 }
        """
        results = {}
        for idx, tx in bag:
            results[idx] = self.execute(tx.payload.sender, tx.contract_name, tx.func_name,
                                        tx.kwargs, auto_commit=False, driver=driver)
            if isinstance(driver, CacheDriver):
                driver.new_tx()
        return results

    def execute(self, sender, contract_name, function_name, kwargs, environment={}, auto_commit=True, driver=None) -> dict:
        """
        Method that does a naive execute

        :param sender:
        :param contract_name:
        :param function_name:
        :param kwargs:
        :return: Dictionary containing the keys 'status_code' 'result' and 'error'
        """
        # Use driver if one is provided, otherwise use the default driver, ensuring to set it
        # back to default only if it was set previously to something else
        if driver:
            runtime.rt.driver = driver

        # A successful run is determined by if the sandbox execute command successfully runs.
        # Therefor we need to have a try catch to communicate success/fail back to the
        # client. Necessary in the case of batch run through bags where we still want to
        # continue execution in the case of failure of one of the transactions.

        environment.update({'__Context': runtime.Context})
        try:
            result = self.sandbox.execute(sender, contract_name, function_name, kwargs, environment)
            status_code = 0
            if auto_commit:
                runtime.rt.driver.commit()
        # TODO: catch SenecaExceptions distinctly, this is pending on Raghu looking into Exception override in compiler
        except Exception as e:
            result = e
            status_code = 1
            runtime.rt.driver.revert()

        self.sandbox.clean()

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


class Sandbox(object):
    def __init__(self):
        install_database_loader()

    def clean(self):
        """
        Convenience method to cleanup the sandbox's imports

        :return:
        """
        runtime.rt.clean_up()

    def execute(self, sender, contract_name, function_name, kwargs, environment={}):

        # __main__ is replaced by the sender of the message in this case
        runtime.rt.ctx.clear()
        runtime.rt.ctx.append(sender)
        runtime.rt.env = environment

        module = importlib.import_module(contract_name)
        #module = __import__(contract_name)

        func = getattr(module, function_name)

        result = func(**kwargs)

        return result


# THIS SHOULD BE USED LATER
class MultiProcessingSandbox(Sandbox):
    def __init__(self):
        super().__init__()
        self.pipe = multiprocessing.Pipe()
        self.p = None

    def terminate(self):
        if self.p is not None:
            self.p.terminate()

    def execute(self, sender, contract_name, function_name, kwargs, environment={}):
        if self.p is None:
            self.p = multiprocessing.Process(target=self.process_loop,
                                             args=(super().execute, ))
            self.p.start()

        _, child_pipe = self.pipe

        # Sends code to be executed in the process loop
        child_pipe.send((sender, contract_name, function_name, kwargs, environment))

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
            sender, contract_name, function_name, kwargs, environment = parent_pipe.recv()
            try:
                result = execute_fn(sender, contract_name, function_name, kwargs, environment={})
                status_code = 0
            except Exception as e:
                result = e
                status_code = 1
            finally:
                parent_pipe.send((status_code, result))

