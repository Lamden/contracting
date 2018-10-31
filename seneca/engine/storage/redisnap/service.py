"""

Interface:

Main process
* new_session() (singleton):
  Returns a session object
  * Methods:
    * finalize()
    * new_transaction(rank_info):
      * creates a process to run executer, forks main process with latest list of other transactions
        * ExecuterBase is subscribed to latest transaction publisher
        * Will throw an exception immediately if a new block is published that causes a conflict.
        * will publish it's own transaction when it's soft-committed and close
      *



Executers, two sides talk over zmq socket:
  * ExClient, started in the client application
    * a connection to the ExServer to run queries
    * a connection to the ExServer that receives errors when higher priority transactions finish and break consistency of view
  * ExServer, forked from main process, it has:
    * a view of current data data, consisting of
      * a list of previously completed transactions, and reads from them
      * a connection to Redis read requests that aren't fulfilled by any transactions fall through to Redis
    * a subscription to receive any higher priority transactions that have completed to either
      * safely insert into its view (not breaking consistency), or
      * send an error message if view consistency in broken





# TODO(s):
* Finish granular address conflict detection
* Operation compaction
* Devise a method to poll for view inconsistencies while smart contracts are running without waiting for db access.
"""
