'''
# Simple tabular datastore #
* Uses myrocks to support SQL operations on rocksdb
* Right now relying on yet to be built execution environment to force squential evaluation of contracts
  * Not doing any concurrency control/transactions. Consistency maintained by that sequential evaluation
* Implementing prototype with SQL alchemy

* Must start work on Seneca import system so we can inject caller address here.
  * Must not be a singleton like standard Python imports because it's very possible this lib will be called by multiple smart contracts in chain and need to give each its own instance
  * Alternatively, it could just always pass smart_contract_id as first arg
  * Caller could just be injected as module-global var

* Need a way tie all mutations smart contract address of caller
  * Probably do not want this for data access

* Maybe provide a transaction interface for performance (or if some kind of parallel execution is eventually allowed.)


* Note: currently no foreign keys allowed in Myrocks, this is a feature under development so we may want to add it when they do.
'''



# TODO: verify this is being called each time it's imported.
#print("loading tabular, TODO: make sure this loads for each and every import")
#print("caller: %s" % seneca_internal.smart_contract_caller)

from itertools import zip_longest
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Sequence, select

# TODO: figure out how we want to handle these.
METADATA = MetaData()
# TODO: Replace this with the real engine from Cilantro


# TODO: restrictions and prefixing tables with smart_contract_caller
# TODO: Don't hard code this

# Note password is auto generated every time docker instance is built, password is hardcoded right now and must be changed to run
# Dockerfile regenerates random password on every build.
ENGINE = create_engine("mysql://seneca_test:enter-your-pw-here@127.0.0.1:3306/seneca_test")
CONN = ENGINE.connect()
METADATA.bind=ENGINE

# http://docs.sqlalchemy.org/en/latest/core/tutorial.html


def outside_table(sc_addr, name):
    """
    Always read-only. To edit another smart_contract's tables, you must use the methods that contract exports

    """
    pass

def run_batch(ops):
    """
    """
    # TODO: This should be implemnted more efficiently than just running each command individually.
    for o in ops:
        o.run()


def tup_defaults(t, prototype):
    return tuple(map(lambda x_y: x_y[0] if x_y[0] else x_y[1], zip_longest(t, prototype)))


class StrLimitLen(object):
    def __init__(self, l):
        self.length_limit = l

def str_len(l):
    return StrLimitLen(l)


# TODO: Validate assumption that this can probably never be secure as implemented
# TODO: This is a preview of an interface, it almost certainly must be implemented
# in something other than Python to be secure, or we'll have to substatially change
# how we eval and run smart contracts
class TTable(object):
    def __init__(self, sa_table):
        self.sa_table = sa_table
        self.call_stack = []

    def run(self):
        temp_ref = self.sa_table
        cs = self.call_stack
        self.call_stack = []

        if cs == ['select']: #Simple and temporary
            return CONN.execute(select([temp_ref]))
        elif cs[0] == 'insert':
            CONN.execute(temp_ref.insert(), cs[1])
        else:
            raise NotImplementedError()

    def select(self):
        self.call_stack.append('select')
        return self

    def insert(self, dict_list):
        self.call_stack.extend(['insert', dict_list])
        return self

    def join(self, with_table, this_on, that_on):
        raise NotImplementedError()


# TODO: function decorator that adds caller data, makes sure it's populated and pre-applies it to name
# @safe_name_prefix
def table(t_name, column_tup_list):
    """
    Create or retrieve table (always prepended with caller smart contract address).
    examples:

    u = st.table('users', [
        ('first_name', str_len(30)),
        ('last_name', str_len(30)),
        ('nick_name', str_len(30), True),
        ('balance', int)
    ])
    # Will always prepend table name with smart contract ID
    # outside_table(sc_addr, name)

    u.update(???).where(???).values(????).run()
    u.insert(????).run()
    u.insert(????).run()
    x = u.select(????).whatever().whatever().run()

    st.run(u.select([u.c.id])
           .where(users.c.id == )

    """
    # TODO: make sure metadata is safely handled and isn't leaking anywhere it shouldn't
    # TODO: Thinking name prefix safety is only for inserts, and drops, confirm.
    # TODO: safely apply whitelist to name, only allow a-z,0-9,_,-  and any mysql rules on names
    # TODO: see if we can restrict users from accessing closure scope on return functions, if we cannot, this must be implemented differently,
    # ultimately we may have to reimplment all this in our own interpreter.

    sc_id = seneca_internal.smart_contract_caller

    assert sc_id is not None, \
      "Something went wrong. This module should only every be called by smart contracts, the caller cannot be identified"

    safe_name = "%s_%s" % (seneca_internal.smart_contract_caller, t_name)
    t_name = None # Unsetting t_name so it cannot accidentally be used
    # Replace this and above logic with decorator function would be better

    def convert_to_sa_type(x):
        if x is int:
            return Integer
        elif type(x) == StrLimitLen:
            return String(x.length_limit)
        else:
            raise ValueError("Unsupported column type.")


    def create_column(c_tup):
        c_name, c_type, unique_con = tup_defaults(c_tup, (None, None, False))
        return Column(c_name, convert_to_sa_type(c_type), unique=unique_con)

    table = Table(safe_name, METADATA ,
       Column('id', Integer, Sequence('user_id_seq'), primary_key=True),
       *map(create_column, column_tup_list),
       # TODO: decide if we actually want autoload enabled
#       autoload_with=ENGINE,
#       check_exists=True,
#       autoload=True
    )

    # TODO: figure out what happens if the table already exists and make changes as needed
#    table.create(ENGINE)
    MetaData.create_all(METADATA, checkfirst=True)

    return TTable(table)







exports = {
    'outside_table': outside_table,
    'run_batch': run_batch,
    'str_len': str_len,
    'table': table,
}
