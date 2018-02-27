'''
# Simple tabular datastore #
* Using sqlite backend for prototype, but keeping interface simple and abstract so it can be switched later
* Right now relying on yet to be built execution environment to force squential evaluation of contracts
  * Not doing any concurrency control/transactions. Consistency maintained by that sequential evaluation
* Defaulting to a sql alchemy-style interface when possible

* Must start work on Seneca import system so we can inject caller address here.
  * Must not be a singleton like standard Python imports because it's very possible this lib will be called by multiple smart contracts in chain and need to give each its own instance
  * Alternatively, it could just always pass smart_contract_id as first arg
  * Caller could just be injected as module-global var

* Need a way tie all mutations smart contract address of caller
  * Probably do not want this for data access

* Maybe provide a transaction interface for performance (or if some kind of parallel execution is eventually allowed.)

'''

# restrict by smart contract caller address
def create_table():
    pass

# restrict by smart contract caller address
def get_table():
    pass


# table object with methods
# select().where(**kwargs).run()
# select().where(**kwargs).limit(5).run()
# select().where(**kwargs).order_by(5).run()
# select().where(**kwargs).order_by(5).desc().run()


# insert(**kwargs).where(**kwargs).run()
#
