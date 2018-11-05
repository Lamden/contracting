# Migration to Redis-compatible datastore #


## Layers of features ##
* Tabular API and Toolbox API
  * Tabular API includes secondary indexes and stuff
* Scratch layer (transactions and save points)
  * Same API as Redis-py
  * Additional methods for transactions and nested transactions

## How do we do transactions and save points? ##
* Note, if we don't write immediately write to Redis, we can assume commands will succeed, but the types must match.
  * E.g. you can't do a hash operation on a string
  * We must verify types before running downstream save points




* How are we doing scratch with atomic incr and decr?
* How are we doing scratch and flush?
* How is scratch structured?
  * Two levels of undo, bins (executer level, and save points)
  * Data structure for save points?
  * How are save points undone?
  * How does caching and cache busting work?

  search from end of list back to beginning, if set, take value and end, if incr/decr, add to stack, if read, ignore, all the way back to end, if needed, access Redis.
  Detailed:
    * Filter each list (in larger list) for matching keys (cacheable against input)
    * Return value if found (cacheable against input)
    * If needed, get from Db (cacheable with tags, look at HermesCache), must be invalidated during flush

### Client side ###
 * Caching reads of deltas and datastore ###
   * Consider implementing dictionary-based LRU cache for Hermes
     * https://pypi.org/project/HermesCache/
     * https://bitbucket.org/saaj/hermes/src/5b814e964b7d0c5644cdc6bd03e596f5c5e7b208/hermes/backend/dict.py?at=default&fileviewer=file-view-default
     * https://pypi.org/project/lru-dict/

## Leveraging Lua eval ##
* Caching
  * EVALSHA  Evaluates a script cached on the server side by its SHA1 digest. Scripts are cached on the server side using the SCRIPT LOAD command. The command is otherwise identical to EVAL.

## Other thoughts ##
* If we use a less durable storage medium, we'll probably want to optimize for fast rebuilds of sections of the db
  * Consider bloom filter on blocks with list of effected contracts
  * Consider a more durable datastore with a list of blocks that have edited each contract
* Redis doesn't have secondary indices, have to roll your own

# Notes on storing tabular data #
* Store rows in hashes contract_id:data_store_name$$primary_key
* Secondary indices must be specified ahead of time
  * Storage methodology
    * k,v for unique
    * set for non-unique
    * Pre-computed query
      * sorted set
      * can use inter and union to get and_ and or_
  * Complex queries
    * Must be predetermined
    * Will be done in Lua
    * Will be sent with a stamp balance
      * If the computed cost exceeds it, it won't be run and an error will be returned.
  *
*

#Tasks#
* KV
  * Audit contracts, see if stuff can be rewritten
  * Spec API

# Notes on proxies #

Redis cluster
dynomite
codis
twemproxy
hash_tag: A two character string that specifies the part of the key used for hashing. Eg "{}" or "$$". Hash tag enable mapping different keys to the same server as long as the part of the key within the tag is the same.

# Possible API to create #
from kv_tabular import *
t = Table([
    ('username', str, primary_key),
    ('password_hash', str, None),
    ('nickname', str, secondary_key),
    ('home_state', str, non_unique_key),
    ('balance', int, in_range),
])

t = Table([
    Column('username', str).primary_key(),
    Column('password_hash', str),
    Column('nickname', str).secondary_key(),
    Column('home_state', str).non_unique_key()),
    Column('balance', int).search_range),
])

t = Table(
    Column('username', str),
    [ Column('password_hash', str),
      Column('nickname', str).unqiue_queryable(),
      Column('home_state', str).queryable()),
      Column('balance', int).queryable_in_range),
    ]
)

has_money = t.get_in_range('balance', 1, 1000)
rich_guys = t.get_in_range('balance', 10000000, None)

californians = t.get_all_equals('home_state', 'California')
gfk = t.get_equals('nickname', 'ghostface killah')

rich_californians = t.and_(
  get_all_equals('home_state', 'California'),
  get_in_range('balance', 10000000, None)
)
