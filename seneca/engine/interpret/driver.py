from walrus.tusks.ledisdb import WalrusLedis
from ledis import Ledis


class Driver(WalrusLedis):
    """
    Connects to the Walrus ORM with Ledis as back-end. We will only allow items that use sets because
    conflict resolution currently does not support
    """


# class Driver(Ledis):
#     pass