import importlib
import multiprocessing
from typing import Dict
import decimal
from contracting.logger import get_logger
from contracting.execution import runtime
from contracting.db.cr.transaction_bag import TransactionBag
from contracting.db.driver import ContractDriver, CacheDriver
from contracting.execution.module import install_database_loader, uninstall_builtins
from contracting import config

#log = get_logger('Executor')


class Executor:
    def __init__(self, production=False, driver=None, metering=True,
                 currency_contract='currency', balances_hash='balances', bypass_privates=False):

        self.metering = metering

        self.driver = driver

        if not self.driver:
            self.driver = ContractDriver()
        self.production = production

        if self.production:
            self.sandbox = MultiProcessingSandbox()
        else:
            self.sandbox = Sandbox()

        self.currency_contract = currency_contract
        self.balances_hash = balances_hash

        self.bypass_privates = bypass_privates

        runtime.rt.env.update({'__Driver': self.driver})

    def execute_bag(self, bag: TransactionBag,
                    auto_commit=False,
                    driver=None,
                    environment={},
                    metering=None) -> Dict[int, tuple]:

        results = self.sandbox.execute_bag(bag,
                                           auto_commit=auto_commit,
                                           driver=driver,
                                           environment=environment,
                                           metering=metering)
        return results

    def execute(self, sender, contract_name, function_name, kwargs,
                environment={},
                auto_commit=True,
                driver=None,
                stamps=1000000,
                metering=None) -> tuple:

        if not self.bypass_privates:
            assert not function_name.startswith(config.PRIVATE_METHOD_PREFIX), 'Private method not callable.'

        if metering is None:
            metering = self.metering

        runtime.rt.env.update({'__Driver': self.driver})

        if driver is None:
            driver = runtime.rt.env.get('__Driver')

        status_code, result, stamps_used = self.sandbox.execute(sender, contract_name, function_name, kwargs,
                                                                auto_commit=auto_commit,
                                                                environment=environment,
                                                                driver=driver,
                                                                metering=metering,
                                                                stamps=stamps,
                                                                currency_contract=self.currency_contract,
                                                                balances_hash=self.balances_hash)

        return status_code, result, stamps_used


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
    def __init__(self, bypass_privates=False):
        install_database_loader()
        self.bypass_privates = bypass_privates

    def wipe_modules(self):
        uninstall_builtins()
        install_database_loader()

    def execute_bag(self, txbag, environment={}, auto_commit=False, driver=None, metering=None):
        response_obj = {}

        for idx, tx in txbag:
            # Each TX is a list of Capnp ContractTransaction structs
            if isinstance(tx.payload.sender, bytes):
                sender = tx.payload.sender.hex()
            else:
                sender = tx.payload.sender

            response_obj[idx] = self.execute(sender,
                                             tx.payload.contractName,
                                             tx.payload.functionName,
                                             tx.payload.kwargs,
                                             auto_commit=auto_commit,
                                             environment=environment,
                                             driver=driver,
                                             metering=metering)
        return response_obj

    def execute(self, sender, contract_name, function_name, kwargs,
                auto_commit=True,
                environment={},
                driver=None,
                metering=None,
                stamps=1000000,
                currency_contract=None,
                balances_hash=None):

        # log.info('Executing with sender {}, contract {}, function {}.'.format(
        #     sender, contract_name, function_name
        # ))
        # log.info('Kwargs: {}'.format(kwargs))
        # log.info('Kwargs type: {}'.format(type(kwargs)))



### EXECUTION START

        # Use _driver if one is provided, otherwise use the default _driver, ensuring to set it
        # back to default only if it was set previously to something else
        if not self.bypass_privates:
            assert not function_name.startswith(config.PRIVATE_METHOD_PREFIX), 'Private method not callable.'

        if driver:
            runtime.rt.env.update({'__Driver': driver})
        else:
            driver = runtime.rt.env.get('__Driver')

        # __main__ is replaced by the sender of the message in this case

        balances_key = None
        if metering:
            balances_key = '{}{}{}{}{}'.format(currency_contract,
                                               config.INDEX_SEPARATOR,
                                               balances_hash,
                                               config.DELIMITER,
                                               sender)

            balance = driver.get(balances_key) or 0

            assert balance * config.STAMPS_PER_TAU >= stamps, 'Sender does not have enough stamps for the transaction. \
                                                       Balance at key {} is {}'.format(balances_key, balance)

        runtime.rt.env.update(environment)
        status_code = 0
        runtime.rt.set_up(stmps=stamps, meter=metering)

        runtime.rt.context._base_state = {
            'signer': sender,
            'caller': sender,
            'this': contract_name,
            'owner': driver.get_owner(contract_name)
        }

        try:
            if runtime.rt.context.owner is not None and runtime.rt.context.owner != runtime.rt.context.caller:
                raise Exception('Caller is not the owner!')

            module = importlib.import_module(contract_name)
            #module = __import__(contract_name)

            func = getattr(module, function_name)

            result = func(**kwargs)

            if auto_commit:
                driver.commit()
        except Exception as e:
            result = e
            status_code = 1
            if auto_commit:
                driver.revert()
        finally:
            if isinstance(driver, CacheDriver):
                driver.new_tx()

### EXECUTION END

        runtime.rt.tracer.stop()

        # Deduct the stamps if that is enabled
        if metering:
            assert balances_key is not None, 'Balance key was not set properly. Cannot deduct stamps.'

            to_deduct = runtime.rt.tracer.get_stamp_used()
            to_deduct /= config.STAMPS_PER_TAU

            to_deduct = decimal.Decimal(to_deduct)

            balance = driver.get(balances_key)

            if balance is None:
                balance = 0

            balance -= to_deduct

            driver.set(balances_key, balance)
            if auto_commit:
                driver.commit()

        stamps_used = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()
        runtime.rt.env.update({'__Driver': driver})

        return status_code, result, stamps_used


# THIS SHOULD BE USED LATER
class MultiProcessingSandbox(Sandbox):
    def __init__(self):
        super().__init__()
        self.pipe = multiprocessing.Pipe()
        self.p = None

    def terminate(self):
        if self.p is not None:
            self.p.terminate()
        self.p = None

    def _lazy_instantiate(self):
        if self.p is None:
            self.p = multiprocessing.Process(target=self.process_loop,
                                             args=(super().execute, ))
            self.p.start()
            self.wipe_modules()

    def _update_driver_cache(self, driver, updated_driver):
        if updated_driver and isinstance(updated_driver, CacheDriver):
            driver.reset_cache(modified_keys=updated_driver.modified_keys,
                               contract_modifications=updated_driver.contract_modifications,
                               original_values=updated_driver.original_values)

    def execute_bag(self, txbag, environment={}, auto_commit=False, driver=None, metering=None):

        self._lazy_instantiate()

        _, child_pipe = self.pipe

        msg = {
            '_driver': driver,
            'txns': {}
        }

        for tx_idx, tx in txbag:
            msg['txns'][tx_idx] = {
                'sender': tx.payload.sender,
                'contract_name': tx.payload.contractName,
                'function_name': tx.payload.functionName,
                'kwargs': tx.payload.kwargs,
                'auto_commit': auto_commit,
                'environment': environment,
                'metering': metering
            }

        child_pipe.send(msg)

        response_obj = child_pipe.recv()
        self._update_driver_cache(driver, response_obj['_driver'])

        return response_obj['results']

    def execute(self, sender, contract_name, function_name, kwargs,
                auto_commit=True,
                environment={},
                driver=None,
                metering=None,
                stamps=1000000,
                currency_contract=None,
                balances_hash=None):

        self._lazy_instantiate()

        _, child_pipe = self.pipe

        # Sends code to be executed in the process loop
        # Create a message of type single execute
        # The reason it is a dictionary with a integer _key is
        # because we may be running a subset of the transactions but
        # still want to maintain order (e.g. 0,1,5)
        msg = {
            '_driver': driver,
            'txns': {
                0: {
                    'sender': sender,
                    'contract_name': contract_name,
                    'function_name': function_name,
                    'kwargs': kwargs,
                    'auto_commit': auto_commit,
                    'environment': environment,
                    'metering': metering,
                    'stamps': stamps,
                    'currency_contract': currency_contract,
                    'balances_hash': balances_hash
                }
            }
        }
        child_pipe.send(msg)

        # Receive result object back from process loop, formatted as
        # (status_code, result), loaded in using dill due to python
        # base pickler not knowning how to pickle module object
        # returned from execute
        response_obj = child_pipe.recv()
        self._update_driver_cache(driver, response_obj['_driver'])
        # In the case mp.execute() is called, we know we only have one
        # entry into the response object
        status_code, result, stamps_used = response_obj['results'][0]

        # Check the status code for failure, if failure raise the result
        return status_code, result, stamps_used

    def process_loop(self, execute_fn):
        parent_pipe, _ = self.pipe
        while True:
            msg = parent_pipe.recv()
            driver = msg['_driver']
            response_obj = {
                '_driver': driver,
                'results': {}
            }
            for tx_idx in sorted(msg['txns'].keys()):
                tx = msg['txns'][tx_idx]
                response_obj['results'][tx_idx] = execute_fn(tx['sender'],
                                                             tx['contract_name'],
                                                             tx['function_name'],
                                                             tx['kwargs'],
                                                             auto_commit=tx['auto_commit'],
                                                             environment=tx['environment'],
                                                             driver=driver)

            parent_pipe.send(response_obj)

