import importlib
from contracting.execution import runtime
from contracting.db.driver import ContractDriver
from contracting.execution.module import install_database_loader, uninstall_builtins, enable_restricted_imports, disable_restricted_imports
from contracting.stdlib.bridge.decimal import ContractingDecimal
from contracting import config
from copy import deepcopy

from logging import getLogger

log = getLogger('CONTRACTING')
import traceback

class Executor:
    def __init__(self, production=False, driver=None, metering=True,
                 currency_contract='currency', balances_hash='balances', bypass_privates=False):

        self.metering = metering

        self.driver = driver

        if not self.driver:
            self.driver = ContractDriver()
        self.production = production

        self.currency_contract = currency_contract
        self.balances_hash = balances_hash

        self.bypass_privates = bypass_privates

        runtime.rt.env.update({'__Driver': self.driver})

    def wipe_modules(self):
        uninstall_builtins()
        install_database_loader()

    def execute(self, sender, contract_name, function_name, kwargs,
                environment={},
                auto_commit=False,
                driver=None,
                stamps=1000000,
                stamp_cost=config.STAMPS_PER_TAU,
                metering=None) -> dict:

        if not self.bypass_privates:
            assert not function_name.startswith(config.PRIVATE_METHOD_PREFIX), 'Private method not callable.'

        if metering is None:
            metering = self.metering

        runtime.rt.env.update({'__Driver': self.driver})

        if driver:
            runtime.rt.env.update({'__Driver': driver})
        else:
            driver = runtime.rt.env.get('__Driver')

        install_database_loader(driver=driver)

        balances_key = None
        try:
            if metering:
                balances_key = '{}{}{}{}{}'.format(self.currency_contract,
                                                   config.INDEX_SEPARATOR,
                                                   self.balances_hash,
                                                   config.DELIMITER,
                                                   sender)

                balance = driver.get(balances_key)
                if balance is None:
                    balance = 0

                assert balance * stamp_cost >= stamps, 'Sender does not have enough stamps for the transaction. \
                                                               Balance at key {} is {}'.format(balances_key,
                                                                                               balance)

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
            func = getattr(module, function_name)

            enable_restricted_imports()
            result = func(**kwargs)
            disable_restricted_imports()

            if auto_commit:
                driver.commit()
        except Exception as e:
            result = e
            tb = traceback.format_exc()
            log.error(str(e))
            log.error(tb)
            status_code = 1
            if auto_commit:
                driver.clear_pending_state()

        ### EXECUTION END

        runtime.rt.tracer.stop()

        # Deduct the stamps if that is enabled
        stamps_used = runtime.rt.tracer.get_stamp_used()

        stamps_used = stamps_used // 1000
        stamps_used += 1
        #stamps_used *= 1000

        if metering:
            assert balances_key is not None, 'Balance key was not set properly. Cannot deduct stamps.'

            to_deduct = stamps_used

            to_deduct /= stamp_cost

            to_deduct = ContractingDecimal(to_deduct)

            balance = driver.get(balances_key)
            if balance is None:
                balance = 0

            balance = max(balance - to_deduct, 0)

            driver.set(balances_key, balance)
                       #mark=False)  # This makes sure that the key isnt modified every time in the block
            if auto_commit:
                driver.commit()

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

