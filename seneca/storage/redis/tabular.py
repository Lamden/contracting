"""
Seneca's redis tabular provides a SQLesce interface with redis as the storage
backend.

TODOs:
Method chains to support:

* select('wallet_id').where(wallet_id=wallet_id).run())
* update(balance=old_balance + amount_to_add).where(wallet_id=wallet_id).run()
* insert(wallet_id=wallet_id, balance=0)
"""


def create_table(table_name, column_spec):

    # Return table
    pass


def get_table(table_name):
    pass


def column(*args, **kwargs):
    pass
