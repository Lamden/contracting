import importlib
import multiprocessing
import decimal
from contracting.logger import get_logger
from . import runtime
from ..db.driver import ContractDriver, CacheDriver
from ..execution.module import install_database_loader, uninstall_builtins
from .. import config

log = get_logger('Executor')


class Executor:
    def __init__(self, production=False, driver=None, metering=True,
                 currency_contract='currency', balances_hash='balances'):

        self.metering = metering

        self.driver = driver

        if not self.driver:
            self.driver = ContractDriver()
        self.production = production

        self.sandbox = Sandbox()

        self.currency_contract = currency_contract
        self.balances_hash = balances_hash

        runtime.rt.env.update({'__Driver': self.driver})

    def execute(self, sender, contract_name, function_name, kwargs,
                environment={},
                auto_commit=True,
                driver=None,
                stamps=1000000,
                metering=None) -> tuple:



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
    def __init__(self):
        install_database_loader()

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

### EXECUTION START

        # Use _driver if one is provided, otherwise use the default _driver, ensuring to set it
        # back to default only if it was set previously to something else
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

        runtime.rt.ctx.clear()
        runtime.rt.ctx.append(sender)
        runtime.rt.env.update(environment)
        status_code = 0
        runtime.rt.set_up(stmps=stamps, meter=metering)
        try:
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

            balance = driver.get(balances_key) or 0
            balance -= to_deduct

            driver.set(balances_key, balance)
            driver.commit()

        stamps_used = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()
        runtime.rt.env.update({'__Driver': driver})

        return status_code, result, stamps_used
