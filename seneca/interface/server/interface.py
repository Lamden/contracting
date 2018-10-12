this is the seneca server interface

# essentially this could be part of a block-manager

- open server socket (using redis)
- this should manage multiple client connections
- maintain redis layer hashmap
  <namespace1> [ <layer0> <layer1> ..]
  <namespace2> [ <layer0> <layer1> ..]

- <layerx> datastructure - redis cache layer
  key    cur-value         mod-value          constraints           txn-list
       (db read once)    (rel-value-sums)       (list)        (sb-index, txn #, rel-value)

- have a fixed db operation api - applies to the latest (top) layer

  # applies to the first (bottom) layer
- support verification (or assertion check) and return a set of appropriate results to the sbbuilders
- support commit to db

