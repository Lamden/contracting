import importlib
from typing import Dict
from contracting.execution import runtime
from contracting.db.cr.transaction_bag import TransactionBag
from contracting.db.driver import ContractDriver
from contracting.execution.module import install_database_loader, uninstall_builtins, enable_restricted_imports, disable_restricted_imports
from contracting.stdlib.bridge.decimal import ContractingDecimal
from contracting import config
from copy import deepcopy

from logging import getLogger

log = getLogger('CONTRACTING')


class Executor:
    def __init__(self, production=False, driver=None, metering=True,
                 currency_contract='currency', balances_hash='balances', bypass_privates=False):

        self.metering = metering

        self.driver = driver

        if not self.driver:
            self.driver = ContractDriver()
        self.production = production

        self.sandbox = Sandbox()

        self.currency_contract = currency_contract
        self.balances_hash = balances_hash

        self.bypass_privates = bypass_privates

        runtime.rt.env.update({'__Driver': self.driver})

    def execute_bag(self, bag: TransactionBag,
                    auto_commit=False,
                    driver=None,
                    environment={},
                    metering=None) -> Dict[int, dict]:

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
                stamp_cost=config.STAMPS_PER_TAU,
                metering=None) -> dict:

        if not self.bypass_privates:
            assert not function_name.startswith(config.PRIVATE_METHOD_PREFIX), 'Private method not callable.'

        if metering is None:
            metering = self.metering

        runtime.rt.env.update({'__Driver': self.driver})

        if driver is None:
            driver = runtime.rt.env.get('__Driver')

        #
        # EXECUTION OUTPUT
        # {
        #     'result': None,
        #     'status_code': None,
        #     'stamps_used': None,
        #     'writes': None, <- list of tuples sorted by key
        #     'deletes': None <- Set
        # }
        #

        output = self.sandbox.execute(sender, contract_name, function_name, kwargs,
                                                                auto_commit=auto_commit,
                                                                environment=environment,
                                                                driver=driver,
                                                                metering=metering,
                                                                stamps=stamps,
                                                                stamp_cost=stamp_cost,
                                                                currency_contract=self.currency_contract,
                                                                balances_hash=self.balances_hash)


        return output


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
        self.bypass_privates = bypass_privates

    def wipe_modules(self):
        uninstall_builtins()
        install_database_loader()

    def execute_bag(self, txbag, environment={}, auto_commit=False, driver=None, metering=None):
        install_database_loader(driver=driver)

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
                driver: ContractDriver=None,
                metering=None,
                stamps=1000000,
                stamp_cost=config.STAMPS_PER_TAU,
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

        #uninstall_builtins()
        install_database_loader(driver=driver)


        # __main__ is replaced by the sender of the message in this case
        balances_key = None
        try:
            if metering:
                balances_key = '{}{}{}{}{}'.format(currency_contract,
                                                   config.INDEX_SEPARATOR,
                                                   balances_hash,
                                                   config.DELIMITER,
                                                   sender)

                balance = driver.get(balances_key)
                if balance is None:
                    balance = 0

                assert balance * stamp_cost >= stamps, 'Sender does not have enough stamps for the transaction. \
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

            if runtime.rt.context.owner is not None and runtime.rt.context.owner != runtime.rt.context.caller:
                raise Exception(f'Caller {runtime.rt.context.caller} is not the owner {runtime.rt.context.owner}!')

            module = importlib.import_module(contract_name)
            #module = __import__(contract_name)

            func = getattr(module, function_name)

            enable_restricted_imports()
            result = func(**kwargs)
            disable_restricted_imports()

            if auto_commit:
                driver.commit()
        except Exception as e:
            result = e
            log.error(str(e))
            status_code = 1
            if auto_commit:
                driver.clear_pending_state()

### EXECUTION END

        runtime.rt.tracer.stop()

        # Deduct the stamps if that is enabled
        if metering:
            assert balances_key is not None, 'Balance key was not set properly. Cannot deduct stamps.'

            to_deduct = runtime.rt.tracer.get_stamp_used()

            to_deduct = to_deduct // 1000
            to_deduct += 1
            to_deduct *= 1000

            to_deduct /= stamp_cost

            to_deduct = ContractingDecimal(to_deduct)

            balance = driver.get(balances_key)
            if balance is None:
                balance = 0

            balance -= to_deduct

            driver.set(balances_key, balance, mark=False) # This makes sure that the key isnt modified every time in the block
            if auto_commit:
                driver.commit()

        stamps_used = runtime.rt.tracer.get_stamp_used()

        stamps_used = stamps_used // 1000
        stamps_used += 1
        stamps_used *= 1000

        runtime.rt.clean_up()
        runtime.rt.env.update({'__Driver': driver})

        output = {
            'status_code': status_code,
            'result': result,
            'stamps_used': stamps_used,
            'writes': deepcopy(driver.pending_writes),
        }

        disable_restricted_imports()

        return output
