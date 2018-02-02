==Supported Types==

Types should be a combination of Python, Cassandra, and Redis supported data types with secondary thought into other
potentially supported systems. Thus:

    Python Types:
        int
        bool
        double <- fixed precision with Decimal library
        string

    Cassandra Types:
        blob / bytes / data
        json / dict?
        timestamp
        uuid
        tuple?

    Redis Types:
        hashmaps / hset, hget
        sets / sset, sget

==Control Flow==

    if / elif / else
    map()
    filter()
    try / except / eventually
    assert

==Data access==

Some light and abstract database access should be available such that the following queries are available:

    select
    insert
    update

    where <conditional?